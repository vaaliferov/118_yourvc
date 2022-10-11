import sys
import torch
from config import *

class YourVC:

    def __init__(self):
        torch.set_grad_enabled(False)
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        sys.path.append(TTS_PATH)
        import TTS.tts, TTS.utils, TTS.config

        cfg = TTS.config.load_config(CONFIG_PATH)
        cfg.model_args['d_vector_file'] = TTS_SPEAKERS_PATH
        cfg.model_args['use_speaker_encoder_as_loss'] = False

        sm_params = {
            'encoder_model_path': CHECKPOINT_SE_PATH, 
            'encoder_config_path': CONFIG_SE_PATH, 
            'use_cuda': torch.cuda.is_available()
        }

        model = TTS.tts.models.setup_model(cfg)
        ap = TTS.utils.audio.AudioProcessor(**cfg.audio)
        sm = TTS.tts.utils.speakers.SpeakerManager(**sm_params)
        
        model.language_manager.set_language_ids_from_file(TTS_LANGUAGES_PATH)
        checkpoint = torch.load(MODEL_PATH, map_location=device)
        model_weights = checkpoint['model'].copy()

        for key in list(model_weights.keys()):
            if 'speaker_encoder' in key:
                del model_weights[key]
        
        model.load_state_dict(model_weights)
        model = model.to(device); model.eval()
        self.ap, self.sm = ap, sm
        self.device = device
        self.model = model

    def convert(self, src_path, trg_path, out_path):  

        torch.set_grad_enabled(False)
        
        src_wav = self.ap.load_wav(src_path).astype('float32')[:2*60*16000]
        trg_wav = self.ap.load_wav(trg_path).astype('float32')[:2*60*16000]
        src_spec = self.ap.spectrogram(src_wav).astype('float32')
        
        src_wav = torch.from_numpy(src_wav).unsqueeze(0)
        trg_wav = torch.from_numpy(trg_wav).unsqueeze(0)
        src_spec = torch.from_numpy(src_spec).unsqueeze(0)

        src_emb = self.sm.speaker_encoder.compute_embedding(src_wav)
        trg_emb = self.sm.speaker_encoder.compute_embedding(trg_wav)
        y_lengths = torch.tensor([src_spec.size(-1)])

        with torch.no_grad():
            out_wav = self.model.voice_conversion(
                src_spec.to(self.device), y_lengths.to(self.device), 
                src_emb.to(self.device), trg_emb.to(self.device))[0].numpy()
            self.ap.save_wav(out_wav, out_path)