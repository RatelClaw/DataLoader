from abc import ABC, abstractmethod
import pandas as pd


class StorageLoaderInterface(ABC):
    """Abstract interface for loading CSV data from different sources."""

    @abstractmethod
    def load_csv(self, path: str) -> pd.DataFrame:
        """Load a CSV file and return a pandas DataFrame."""
        pass
