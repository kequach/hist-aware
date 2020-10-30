# pipeline_text_selection.py
"""
This script contains the pipeline to select the first naive text
selection on the delpher dataset
"""
import os
from sys import getsizeof

from datetime import datetime
from pathlib import Path
from loguru import logger
import pandas as pd
import numpy as np
from pyfiglet import Figlet

# Import modules
from iterators import (
    iterate_directory,
    iterate_metadata,
    iterate_files,
    ungzip_metdata,
    iterate_directory_gz,
)
from text_selection import select_articles

# Just some code to print debug information to stdout
np.set_printoptions(threshold=100)


class TextSelection:
    def __init__(
        self,
        FILE_PATH: Path,
        DIR_PATH: Path,
        SAVE_PATH: Path,
        UNGIZP: bool,
        DATAFILE: dict,
        KEYWORDS: str,
        NLP: object,
        # NUM_SYNONYMS,
    ) -> None:
        self.FILE_PATH = FILE_PATH
        self.DIR_PATH = DIR_PATH
        self.SAVE_PATH = SAVE_PATH
        self.UNGIZP = UNGIZP
        self.DATAFILE = DATAFILE
        self.KEYWORDS = KEYWORDS
        # self.NUM_SYNONYMS = NUM_SYNONYMS
        self.NLP = NLP

        f = Figlet(font="slant")
        print(f.renderText("HistAware"))

    def ungzip_metadata_files(self) -> None:
        """If true ungizp the metadata files in data/raw"""

        # TODO: make the ungizip iterate over the entire data
        logger.debug("Ungzipping metadata")
        ungzip_metdata(dir_path=self.DIR_PATH, file_type=".gz")

    # TODO: Create two functions out of this
    def iterate_directories(self) -> None:
        """Iterate directories to catalogue files"""
        if not os.path.isfile(
            os.path.join(self.SAVE_PATH, "file_info", "article_info.csv")
        ):
            # Iterate in the directory and retrieve all the xml article names
            logger.debug("Retrieving article information")
            xml_article_names = iterate_directory(
                dir_path=self.DIR_PATH, file_type=".xml"
            )
            self.article_names = pd.DataFrame.from_dict(xml_article_names)
            self.article_names.reset_index(inplace=True)

            logger.debug(f"Size of directory list {getsizeof(self.article_names)}")
            self.article_names.to_csv(
                os.path.join(self.SAVE_PATH, "file_info", "article_info.csv")
            )
            logger.debug("Articles list saved")
        else:
            logger.debug("Articles list already exists. Skipping")

        # Iterate in the directory and retrieve all the names of the metadata
        if not os.path.isfile(
            os.path.join(self.SAVE_PATH, "file_info", "metadata_info.csv")
        ):
            logger.debug("Retrieving metadata information")
            gz_metadata_files = iterate_directory_gz(
                dir_path=self.DIR_PATH, file_type=".gz"
            )
            self.metadata_files = pd.DataFrame.from_dict(gz_metadata_files)
            self.metadata_files.reset_index(inplace=True)

            logger.debug(f"Size of metadata list {getsizeof(self.metadata_files)}")
            self.metadata_files.to_csv(
                os.path.join(self.SAVE_PATH, "file_info", "metadata_info.csv")
            )
            logger.debug("Metadata list saved")
        else:
            logger.debug("Articles list already exists. Skipping")

    def process_metdata(self, save_path, files) -> None:
        if self.DATAFILE["metadata"] == "True":
            logger.debug("Processing and saving metadata to csv of metadata")
            iterate_metadata(save_path, files)
        else:
            logger.debug("Metadata already processed. Skipping.")

    def process_articles(self, save_path, files) -> None:
        if self.DATAFILE["files"] == "True":
            logger.debug("Processing and saving articles to csv of articles")
            iterate_files(save_path, files)
        else:
            logger.debug("Articles already processed. Skipping.")

    def process_files(self) -> None:
        """If DATAFILE is True, then process and save the files.
        This process is extremely time-intensive, so it should be done only once."""

        if self.DATAFILE["start"] == "True":
            # Load and process articles
            self.article_names = pd.read_csv(
                os.path.join(self.SAVE_PATH, "file_info", "article_info.csv")
            )
            self.process_articles(save_path=self.SAVE_PATH, files=self.article_names)

            # Load and process metadata
            self.metadata_files = pd.read_csv(
                os.path.join(self.SAVE_PATH, "file_info", "metadata_info.csv")
            )
            self.process_metdata(save_path=self.SAVE_PATH, files=self.metadata_files)
        else:
            logger.debug(
                "Skipping processing of both articles and metadata. If you want to \
                change it check the settings."
            )

    def retrieved_saved_files(self) -> None:
        """Retrieve path and name of saved data"""

        logger.debug("Find path and name of saved articles")
        self.csv_articles = iterate_directory(
            dir_path=os.path.join(self.SAVE_PATH, "processed_articles"),
            file_type=".csv",
        )
        self.csv_articles = pd.DataFrame(self.csv_articles)
        self.csv_articles.rename(
            {
                "article_name": "csv_name",
                "article_path": "csv_path",
                "article_dir": "csv_dir",
            },
            axis=1,
            inplace=True,
        )

        logger.debug("Find path and name of saved metadata")
        self.csv_metadata = iterate_directory(
            dir_path=os.path.join(self.SAVE_PATH, "processed_metadata"),
            file_type=".csv",
        )
        self.csv_metadata = pd.DataFrame(self.csv_metadata)
        self.csv_metadata.rename(
            {
                "article_name": "csv_name",
                "article_path": "csv_path",
                "article_dir": "csv_dir",
            },
            axis=1,
            inplace=True,
        )

    def search_synonyms(self) -> None:
        """Using the processed and saved data, search the synonyms"""
        li = []

        for index, row in self.csv_metadata.iterrows():
            csv_file = pd.read_csv(row["csv_path"])
            li.append(csv_file)

        self.df_metadata = pd.concat(li, axis=0)
        self.df_metadata.drop(["level_0", "date"], axis=1, inplace=True)
        self.df_metadata.rename(
            {"filepath": "metadata_filepath", "index": "index_metadata"},
            axis=1,
            inplace=True,
        )

        # Search synonyms in saved articles
        li = []
        logger.info("Searching keywords")
        for i, row in self.csv_articles.iterrows():
            csv_file = pd.read_csv(row["csv_path"])
            li.append(csv_file)
            if i % 5 == 0:
                # Iterate 250.000 articles at the time
                df_articles = pd.concat(li, axis=0)
                df_articles.sort_values(by=["index"], ascending=True)
                df_articles.rename(
                    {"filepath": "article_filepath", "index": "index_article"},
                    axis=1,
                    inplace=True,
                )
                df_joined = df_articles.merge(self.df_metadata, how="left", on="dir")

                # iterate through list of lists of syn

                for keyword in self.KEYWORDS:
                    logger.debug(f"Searching dataset using: {keyword}")
                    selected_art = select_articles(
                        nlp=self.NLP,
                        word=keyword,
                        df=df_joined,
                        # n=self.NUM_SYNONYMS
                    )
                    today = datetime.now()
                    NAME = str(today.date()) + "_" + keyword + ".csv"

                    selected_art.to_csv(
                        os.path.join(self.SAVE_PATH, "selected_articles", NAME),
                        sep=",",
                        quotechar='"',
                        index=False,
                    )

                # Reset list of saved csv to zero
                selected_art = []
