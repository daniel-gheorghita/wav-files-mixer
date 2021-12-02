from scipy.io import wavfile
import os
from config import Config
import numpy as np
import copy
from tqdm import tqdm

def combine_wavs (FS, wav_original, wav_to_add, clean_start, clean_end, duration, mixing_ratio_db):
    wav_to_add_adjusted = copy.deepcopy(wav_to_add)
    if np.size(wav_to_add_adjusted) / FS < (duration - clean_start - clean_end):
        ratio_length = int((duration - clean_start - clean_end) / (np.size(wav_to_add) / FS))
        wav_to_add_adjusted = np.tile(wav_to_add, ratio_length + 1)
    else:
        wav_to_add_adjusted = wav_to_add_adjusted[0: duration * FS]

    normalize_to_16b_factor = (2 ** 15) / np.max(wav_to_add_adjusted)
    wav_to_add_adjusted = (wav_to_add_adjusted * normalize_to_16b_factor).astype(np.int16)

    wav_original_adjusted = wav_original[0:duration*FS]
    normalize_to_16b_factor = (2 ** 15) / np.max(wav_original_adjusted)
    wav_original_adjusted = (wav_original_adjusted * normalize_to_16b_factor).astype(np.int16)

    mixing_ratio = 10 ** (mixing_ratio_db/10)
    wav_original_adjusted[clean_start * FS : -clean_end*FS] = wav_original_adjusted[clean_start * FS : -clean_end*FS]/np.sqrt(mixing_ratio) + \
                wav_to_add_adjusted[0:FS*(duration-clean_start-clean_end)]
    normalize_to_16b_factor = (2 ** 15) / np.max(wav_original_adjusted)
    wav_original_adjusted = (wav_original_adjusted * normalize_to_16b_factor).astype(np.int16)

    return wav_original_adjusted

def main(config):
    wav_file_to_add = config.input_wav
    sample_rate_wav_to_add, wav_to_add = wavfile.read(wav_file_to_add)

    wav_files_original = os.listdir(config.input_folder)
    wav_files_original = [wav_file for wav_file in wav_files_original if wav_file.split('.')[-1] == 'wav']

    for wav_file_original in tqdm(wav_files_original):
        sample_rate_wav_original, wav_original = wavfile.read(os.path.join(
                                                            os.path.join(
                                                                os.path.dirname(__file__), 
                                                                config.input_folder), 
                                                                wav_file_original))

        if sample_rate_wav_to_add != sample_rate_wav_original:
            print("!!! Sample rates are different. This case is not handled. Skipping...")
            continue

        for clean_start in config.clean_seconds_start:
            for clean_end in config.clean_seconds_end:
                for duration in config.total_duration_seconds:
                    for mix_ratio_db in config.mixing_ratios_db:

                        if duration > 60 * sample_rate_wav_original:
                            print("!!! Desired final duration {}s is longer than the original duration. This case is not handled. Skipping...".format(duration))
                            continue
                
                        wav_output = combine_wavs(sample_rate_wav_original, wav_original, wav_to_add,
                                                    clean_start, clean_end, duration, mix_ratio_db)
                        output_filename = "{}_{}s_{}s_{}s_{}db.wav".format(wav_file_original.split('.')[0], clean_start, clean_end, duration, mix_ratio_db)
                        output_filepath = os.path.join(
                                            config.output_folder, 
                                            output_filename)
                        wavfile.write(output_filepath, sample_rate_wav_original, wav_output)

    

if __name__ == "__main__":
    config = Config(file=os.path.join(os.path.dirname(__file__), "config.ini"))

    print(config.__dict__)
    main(config)
