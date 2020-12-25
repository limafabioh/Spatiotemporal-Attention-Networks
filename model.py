import torch
from torch import nn
import torch.cuda as cuda
from EncoderDecoder import Encoder, Encoder2, Decoder
from module import Attn

# Hyper Parameters

BATCH = 300
EPOCHS = 40
INPUT_SIZE = 6
LR = 0.01
d_model = 512
heads = 8
HIDDEN_SIZE = 32
h_state = None
TIME_STEP = 12
STEPS = 1
DEVICE = torch.device('cuda' if cuda.is_available() else 'cpu')


class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.encoder = Encoder()
        self.encoder2 = Encoder2()
        self.decoder = Decoder()
        self.attn = Attn(HIDDEN_SIZE)
        self.concat = nn.Linear(HIDDEN_SIZE * 2, HIDDEN_SIZE)
        self.out = nn.Linear(HIDDEN_SIZE, 1)

    def forward(self, input):
        input_T = input.transpose(1, 2).to(DEVICE)
        batch = input_T.size()[0]
        outputs = torch.zeros(TIME_STEP, batch, d_model).to(DEVICE)
        for k in range(TIME_STEP):
            x = input_T[:, :, k].unsqueeze(2)
            output = self.encoder(x)
            outputs[k] = output.permute(1, 0, 2)

        outputs = outputs.permute(1, 0, 2)

        encoder_output, encoder_hidden = self.encoder2(outputs, None)
        decoder_hidden = encoder_hidden

        temp = torch.zeros_like(input[:, -1].unsqueeze(1)).to(DEVICE)
        out, hidden, decoder_output = self.decoder(temp, decoder_hidden)

        energies = self.attn(hidden, encoder_output)
        context = energies.bmm(encoder_output)
        concat_input = torch.cat((decoder_output.squeeze(), context.squeeze()), dim=1)
        concat_output = torch.tanh(self.concat(concat_input))
        pred = self.out(concat_output)

        return pred
