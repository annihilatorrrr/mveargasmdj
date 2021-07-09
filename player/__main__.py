import time
import shutil
import logging
import asyncio
import datetime
import pytgcalls
from pathlib import Path
from pyrogram import idle, raw
from player.telegram import Audio_Master, voice_chat
from player.helpers.ffmpeg_handler import merge_files
from player.telegram.audio_handler import download_random_messages

raw_file_path = None

async def main():
    global raw_file_path
    await Audio_Master.start()
    while not Audio_Master.is_connected:
        await asyncio.sleep(1)

    audio_download_path = await download_random_messages(1)

    master_loop = asyncio.get_event_loop()
    proc_merge_files = master_loop.run_in_executor(None, merge_files, audio_download_path)
    resp_merge_files = await proc_merge_files

    initiate_time = time.time()
    raw_file = resp_merge_files['raw_file']

    group_call = pytgcalls.GroupCall(Audio_Master, raw_file)
    await group_call.start(voice_chat)
    logging.info(f"Playing mix of duration {str(datetime.timedelta(seconds=resp_merge_files['duration']))}")

    while True:
        await asyncio.sleep(1)
        if (time.time() - initiate_time) > (resp_merge_files['duration'] - 20):
            audio_download_path = await download_random_messages(1)
            master_loop = asyncio.get_event_loop()
            proc_merge_files = master_loop.run_in_executor(None, merge_files, audio_download_path)
            resp_new_merge_files = await proc_merge_files
            
            new_raw_file = resp_new_merge_files['raw_file']
            initiate_time = time.time()
            
            await asyncio.sleep(10)
            logging.info(f"Playing mix of duration {str(datetime.timedelta(seconds=resp_new_merge_files['duration']))}")
            group_call.input_filename = new_raw_file

            raw_file_path = Path(raw_file)
            if raw_file_path.exists():
                shutil.rmtree(raw_file_path.parent)

            raw_file = new_raw_file

    
    await idle()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt as e:
        loop.stop()
    finally:
        if raw_file_path:
            logging.info("Removing temporary files and closing the loop!")
            if raw_file_path.exists():
                shutil.rmtree(raw_file_path.parent)
