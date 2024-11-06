import asyncio
import aiofile

from amazon_transcribe.client import TranscribeStreamingClient, CredentialRevolver
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent


async def parse_int(file, byte_length=4):
    chunk = await file.read(byte_length)
    return int.from_bytes(chunk, 'little')


async def parse_wav_metadata(file):
    riff = await file.read(4)
    assert riff == b'RIFF'

    overall_size = await parse_int(file)

    wave = await file.read(4)
    assert wave == b'WAVE'

    fmt = await file.read(4)
    assert fmt == b'fmt '

    fmt_data_len = await parse_int(file)
    fmt_type = await parse_int(file, byte_length=2)
    num_channels = await parse_int(file, byte_length=2)
    sample_rate = await parse_int(file)
    byte_rate = await parse_int(file)
    block_align = await parse_int(file, byte_length=2)
    bits_per_sample = await parse_int(file, byte_length=2)

    # Byte rate should equal (Sample Rate * BitsPerSample * Channels) / 8
    assert (sample_rate * bits_per_sample * num_channels) / 8 == byte_rate

    data_header = await file.read(4)
    assert data_header == b'data'

    data_len = await parse_int(file)

    wav_metadata = {
        'OverallSize': overall_size,
        'FormatLength': fmt_data_len,
        'FormatType': fmt_type,
        'Channels': num_channels,
        'SampleRate': sample_rate,
        'ByteRate': byte_rate,
        'BlockAlign': block_align,
        'BitsPerSample': bits_per_sample,
        'DataLength': data_len,
    }

    return wav_metadata


async def rate_limit(file, byte_rate):
    chunk = await file.read(byte_rate)
    loop = asyncio.get_event_loop()
    last_yield_time = -1.0  # -1 to allow the first yield immediately
    while chunk:
        time_since_last_yield = loop.time() - last_yield_time
        if time_since_last_yield < 1.0:
            # Only yield once per second at most, compensating for how long
            # between the last yield it's been
            await asyncio.sleep(1.0 - time_since_last_yield)
        last_yield_time = loop.time()
        yield chunk
        chunk = await file.read(byte_rate)


class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                print(alt.transcript)


async def write_chunks(stream, f, wav_metadata):
    async for chunk in rate_limit(f, wav_metadata['ByteRate']):
        await stream.input_stream.send_audio_event(audio_chunk=chunk)
    await stream.input_stream.end_stream()


async def basic_transcribe(filepath):
    # Setup up our client with our chosen AWS region
    client = TranscribeStreamingClient(
        region="us-west-2")

    async with aiofile.async_open(filepath, 'rb') as f:
        wav_metadata = await parse_wav_metadata(f)

        # Start transcription to generate our async stream
        stream = await client.start_stream_transcription(
            language_code="en-US",
            media_sample_rate_hz=wav_metadata['SampleRate'],
            media_encoding="pcm",
        )

        # Instantiate our handler and start processing events
        await asyncio.gather(
            write_chunks(stream, f, wav_metadata),
            MyEventHandler(stream.output_stream).handle_events(),
        )


loop = asyncio.get_event_loop()
loop.run_until_complete(basic_transcribe('test.wav'))
loop.close()
