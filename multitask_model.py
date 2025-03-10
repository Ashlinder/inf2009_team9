import torch
import torch.nn as nn

# Two output heads: one for binary classification and one for multi-class classification
class MultiTaskModel(nn.Module):
    def __init__(self, base_model, num_classes):
        super(MultiTaskModel, self).__init__()
        self.base_model = base_model
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.binary_classifier = nn.Sequential(
            nn.Linear(base_model.last_channel, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 1),  # Binary classification
            nn.Sigmoid()  # Apply sigmoid activation
        )
        self.multi_classifier = nn.Sequential(
            nn.Linear(base_model.last_channel, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes),  # Multi-class classification
            nn.LogSoftmax(dim=1)  # Apply softmax activation
        )

    def forward(self, x):
        x = self.base_model.features(x)
        x = self.global_pool(x)
        x = torch.flatten(x, 1)
        binary_output = self.binary_classifier(x)
        multi_output = self.multi_classifier(x)

        return binary_output, multi_output