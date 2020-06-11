# Copyright 2017 Neural Networks and Deep Learning lab, MIPT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from logging import getLogger
from random import Random
from typing import Dict, Iterator, List, Tuple

from sklearn.model_selection import train_test_split

from deeppavlov.core.common.registry import register
from deeppavlov.core.data.data_learning_iterator import DataLearningIterator

log = getLogger(__name__)


@register('multitask_iterator')
class MultiTaskIterator:
    """
    Class gets data dictionary from DatasetReader instance, merge fields if necessary, split a field if necessary

    Args:
        data: dictionary of data with fields "train", "valid" and "test" (or some of them)
        fields_to_merge: list of fields (out of ``"train", "valid", "test"``) to merge
        merged_field: name of field (out of ``"train", "valid", "test"``) to which save merged fields
        field_to_split: name of field (out of ``"train", "valid", "test"``) to split
        split_fields: list of fields (out of ``"train", "valid", "test"``) to which save splitted field
        split_proportions: list of corresponding proportions for splitting
        seed: random seed for iterating
        shuffle: whether to shuffle examples in batches
        split_seed: random seed for splitting dataset, if ``split_seed`` is None, division is based on `seed`.
        stratify: whether to use statified split
        *args: argument
        **kwargs: arguments

    Attributes:
        data: dictionary of data with fields "train", "valid" and "test" (or some of them)
    """

    def __init__(self, data: dict, seed: int = None, shuffle: bool = True, *args, **kwargs):
        """
        Initialize dataset using data from DatasetReader,
        merges and splits fields according to the given parameters.
        """
        self.iterators = data
        self.shuffle = shuffle

        self.random = Random(seed)

        self.train = self._extract_data_type('train')
        self.valid = self._extract_data_type('valid')
        self.test = self._extract_data_type('test')
        self.data = {
            'train': self.train,
            'valid': self.valid,
            'test': self.test,
            'all': self._unite_dataset_parts(self.train, self.valid, self.test)
        }

    def _extract_data_type(self, data_type):
        dataset_part = {}
        for task, iterator in self.iterators.items():
            dataset_part[task] = getattr(iterator, data_type)
        return dataset_part

    @staticmethod
    def _unite_dataset_parts(*dataset_parts):
        united = {}
        for ds_part in dataset_parts:
            for task, data in ds_part.items():
                if task not in united:
                    united[task] = data
                else:
                    united[task] = united[task] + data
        return united

    def gen_batches(self, batch_size: Dict[str, int], data_type: str = 'train',
                    shuffle: bool = None) -> Iterator[Dict[str, Tuple[tuple, tuple]]]:
        batch_generators = {
            task: self.iterators[task].gen_batches(bs, data_type, shuffle) for task, bs in batch_size.items()}
        while True:
            batch = {}
            try:
                for task, gen in batch_generators.items():
                    batch[task] = next(gen)
            except StopIteration:
                break
            yield batch

    def get_instances(self, data_type: str = 'train'):
        x_instances = []
        y_instances = []
        for task, it in self.iterators.items():
            x, y = zip(*it.data[data_type])
            x_instances.append(x)
            y_instances.append(y)
        return tuple(x_instances + y_instances)
