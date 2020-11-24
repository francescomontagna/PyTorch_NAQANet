import torch
import torch.nn as nn

from code.modules.encoder.encoder import EncoderBlock
from code.modules.encoder.depthwise_conv import DepthwiseSeparableConv
from code.modules.pointer import Pointer
from code.modules.cq_attention import CQAttention
from code.modules.embeddings import Embedding
from code.modules.utils import set_mask
from code.util import torch_from_json
from code.args import get_train_args
from code.model.qanet import QANet


class NAQANet(QANet):
    def __init__(self, 
                 device,
                 word_embeddings,
                 char_embeddings,
                 w_emb_size:int = 300,
                 c_emb_size:int = 64,
                 hidden_size:int = 128,
                 c_max_len: int = 800,
                 q_max_len: int = 100,
                 p_dropout: float = 0.1,
                 num_heads : int = 8, 
                 answering_abilities = ['passage_span_extraction', 'counting', 'addition_subtraction'],
                 max_count = 10): # max number the network can count
        """
        :param hidden_size: hidden size of representation vectors
        :param q_max_len: max number of words in a question sentence
        :param c_max_len: max number of words in a context sentence
        :param p_dropout: dropout probability
        """
        QANet.__init__(
                word_embeddings,
                char_embeddings,
                w_emb_size = 300,
                c_emb_size = 64,
                hidden_size = 128,
                c_max_len = 800,
                q_max_len = 100,
                p_dropout = 0.1,
                num_heads = 8)

        # NUMERICALLY AUGMENTED OUTPUT

        # pasage and question representations coefficients
        self.passage_weights_layer = nn.Linear(hidden_size, 1)
        self.question_weights_layer = nn.Linear(hidden_size, 1)

        # answer type predictor
        if len(self.answering_abilities) > 1:
            self.answer_ability_predictor = nn.Sequential(
                nn.Linear(2*hidden_size, hidden_size),
                nn.ReLu(), 
                nn.Dropout(p = self.p_dropout),
                nn.Linear(hidden_size, len(self.answering_abilities)),
                nn.ReLu(), 
                nn.Dropout(p = self.p_dropout)
            ) # then, apply a softmax

        

        if 'passage_span_extraction' in self.answering_abilities:
            self.passage_span_start_predictor = nn.Sequential(
                nn.Linear(hidden_size * 2, hidden_size),
                nn.ReLu(), 
                nn.Linear(hidden_size, 1),
                nn.ReLu()
            )
            self.passage_span_end_predictor = FeedForward(
                nn.Linear(hidden_size * 2, hidden_size),
                nn.ReLu(), 
                nn.Linear(hidden_size, 1),
                nn.ReLu()
            ) # then, apply a softmax

        if 'counting' in self.answering_abilities:
            self.count_number_predictor = nn.Sequential(
                nn.Linear(hidden_size, hidden_size),
                nn.ReLu(), 
                nn.Dropout(p = self.p_dropout),
                nn.Linear(hidden_size, self.max_count),
                nn.ReLu()
            ) # then, apply a softmax
        
        if 'addition_subtraction' in self.answering_abilities:
            self.number_sign_predictor = nn.Sequential(
                nn.Linear(hidden_size*3, hidden_size),
                nn.ReLu(),
                nn.Linear(hidden_size, 3),
                nn.ReLu()
            )

    def forward(self, cw_idxs, cc_idxs, qw_idxs, qc_idxs):

        M0, M1, M2   = QANet.forward(cw_idxs, cc_idxs, qw_idxs, qc_idxs)

        print(self.passage_aware)

        # The first modeling layer is used to calculate the vector representation of passage
        passage_representation = passage_weights_layer(self.passage_aware)


        pass


if __name__ == "__main__":
    test = False
    torch.emp

    if test:

        torch.manual_seed(32)
        batch_size = 4
        q_max_len = 5
        c_max_len = 7
        wemb_vocab_size = 9
        emb_size = 300
        hidden_size = 128
        dropout_prob = 0.1
        device = 'cpu'
        args = get_train_args()
        word_embeddings = torch_from_json(args.word_emb_file)

        # define model
        model = QANet(device, word_embeddings)

        # fake dataset
        question_lengths = torch.LongTensor(batch_size).random_(1, q_max_len)
        question_wids = torch.zeros(batch_size, q_max_len).long()
        context_lengths = torch.LongTensor(batch_size).random_(1, c_max_len)
        context_wids = torch.zeros(batch_size, c_max_len).long()

        for i in range(batch_size):
            question_wids[i, 0:question_lengths[i]] = \
                torch.LongTensor(1, question_lengths[i]).random_(
                    1, wemb_vocab_size)

            context_wids[i, 0:context_lengths[i]] = \
                torch.LongTensor(1, context_lengths[i]).random_(
                    1, wemb_vocab_size)

        p1, p2 = model(context_wids, question_wids)

        yp1 = torch.argmax(p1, 1)
        yp2 = torch.argmax(p2, 1)
        yps = torch.stack([yp1, yp2], dim=1)
        print(f"yp1 {yp1}")
        print(f"yp2 {yp2}")
        print(f"yps {yps}")

        ymin, _ = torch.min(yps, 1)
        ymax, _ = torch.max(yps, 1)
        print(f"ymin {ymin}")
        print(f"ymax {ymax}")