import os
import gzip
import shutil

import pandas as pd
from loguru import logger
from itertools import chain

import parsers


def iterate_directory(dir_path, file_type):
    """Iterate over the `path_dir` and its children and
    create a dictionary of
        - name
        - path
        - dir
    names of files found
    """
    file_names = {}
    list_names = []

    for subdir, dirs, files in os.walk(dir_path, topdown=True):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(str(file_type)):
                file_names["article_name"] = file
                file_names["article_path"] = filepath
                file_names["article_dir"] = subdir
                list_names.append(file_names)
                file_names = {}

    return list_names


def iterate_directory_gz(dir_path, file_type):
    """Iterate over the `path_dir` and its children and
    create a dictionary of
        - name
        - path
        - dir
        - content
    of .gz files found.
    """
    gz_content = {}
    list_gzs = []

    for subdir, dirs, files in os.walk(dir_path, topdown=True):
        for file in files:
            filepath = subdir + os.sep + file
            if filepath.endswith(str(file_type)):
                # Create list of dict
                # TODO: TO CHECK that if f is not used it's not a problem
                # This should iterate on the opened xml file
                with gzip.open(filepath, "rb") as f:
                    gz_content["metadata_name"] = file + ".xml"
                    gz_content["metadata_path"] = filepath + ".xml"
                    gz_content["metadata_dir"] = subdir

                    list_gzs.append(gz_content)
                    gz_content = {}

    return list_gzs


def ungzip_metdata(dir_path, file_type):
    """Iterate over the `path_dir` and its children and
    ungizp the .gz metadata files found.
    """

    for subdir, dirs, files in os.walk(dir_path, topdown=True):
        for file in files:
            # logger.debug(f"{file}")
            filepath = subdir + os.sep + file
            if filepath.endswith(str(file_type)):
                with gzip.open(filepath, "rb") as f, open(filepath + ".xml", "wb") as r:
                    shutil.copyfileobj(f, r, 65536)


def iterate_files(
    save_path,
    files,
    save_each=50000,
    progress_each=10000,
    restart=False,
    index_restart=0,
):
    """Iterate through files `files`, parse them and concatenate
    the result to be saved as a DataFrame in a csv object (.ftr)

    To restart the iteration, set `restart=True` and select the index from which the
    iteration should restart with `index_restart`.
    """
    list_articles = []

    if restart is False:
        main = None
        previous_i = 0
        current_i = 0
        i = 0
        cnt = 0
        for index, row in files.iterrows():
            try:
                list_articles.append(
                    parsers.parse_XML_article(
                        path=row["article_path"],
                        art_dir=row["article_dir"],
                        title=row["article_name"],
                        index=row["index"],
                    )
                )
            except Exception as e:
                logger.debug(f"Index: {index}", e.args)
                continue
            # Each X, save the file in a .csv
            if i == save_each:
                current_i = current_i + i
                # TODO: Here potential path problem
                file_path = os.path.join(
                    save_path,
                    "processed_data_list_"
                    + str(previous_i)
                    + "_"
                    + str(current_i)
                    + ".csv",
                )
                main = pd.DataFrame(list(chain.from_iterable(list_articles)))
                main.to_csv(file_path)
                main = None
                list_articles = []
                previous_i = current_i
                i = 0
            # Each 10000 files, print the progress
            if i % progress_each == 0:
                # clear_output(wait=True)
                logger.debug("Files parsed: " + str(progress_each * cnt))
                logger.debug(
                    "Current file: "
                    + row["article_name"]
                    + " (Index: "
                    + str(row["index"])
                    + ")"
                )
                cnt += 1
            i += 1
    if restart is True:
        main = None
        previous_i = index_restart
        current_i = index_restart
        i = 0
        cnt = index_restart / progress_each
        list_articles = []
        for index, row in files.iloc[index_restart:].iterrows():
            try:
                list_articles.append(
                    parsers.parse_XML_article(
                        path=row["article_path"],
                        art_dir=row["article_dir"],
                        title=row["article_name"],
                        index=row["index"],
                    )
                )
            except Exception as e:
                logger.debug(f"Index: {index}", e.args)
                continue
            # Each X, save the file in a .ftr
            if i == save_each:
                current_i = current_i + i
                file_path = os.path.join(
                    save_path,
                    "processed_data_list_"
                    + str(previous_i)
                    + "_"
                    + str(current_i)
                    + ".csv",
                )
                main = pd.DataFrame(list(chain.from_iterable(list_articles)))
                main.to_csv(file_path)
                main = None
                list_articles = []
                previous_i = current_i
                i = 0
            # Each 1000 files, print the progress
            if i % progress_each == 0:
                # clear_output(wait=True)
                logger.debug("Files parsed: " + str(progress_each * cnt))
                logger.debug(
                    "Current file: "
                    + row["article_name"]
                    + "(Index: "
                    + str(row["index"])
                    + ")"
                )
                cnt += 1
            i += 1


def iterate_metadata(
    save_path, files, save_each=1000, progress_each=1000, restart=False, index_restart=0
):
    """Iterate through files `metadata`, parse them and concatenate
    the result to be saved as a DataFrame in a csv object (.csv)

    To restart the iteration, set `restart=True` and select the index from which the
    iteration should restart with `index_restart`.
    """
    list_metadata = []

    if restart is False:
        main = None
        previous_i = 0
        current_i = 0
        i = 0
        cnt = 0
        list_metadata = []
        for index, row in files.iterrows():
            try:
                list_metadata.append(
                    parsers.parse_XML_metadata(
                        path=row["metadata_path"],
                        met_dir=row["metadata_dir"],
                        title=row["metadata_name"],
                        index=row["index"],
                    )
                )
            except Exception:
                # logger.debug(f"Something missing at index: {index}")
                continue
            # Each X, save the file in a .csv
            if i == save_each:
                current_i = current_i + i
                file_path = os.path.join(
                    save_path,
                    "processed_metadata_"
                    + str(previous_i)
                    + "_"
                    + str(current_i)
                    + ".csv",
                )
                main = pd.DataFrame(list(chain.from_iterable(list_metadata)))
                # main = pd.DataFrame.from_dict(dict_metadata).T.reset_index()
                main.to_csv(file_path)
                main = None
                list_metadata = []
                previous_i = current_i
                i = 0
            # Each 100 files, print the progress
            if i % progress_each == 0:
                # clear_output(wait=True)
                logger.debug("Files parsed: " + str(progress_each * cnt))
                logger.debug(
                    "Current file: "
                    + row["metadata_name"]
                    + " (Index: "
                    + str(row["index"])
                    + ")"
                )
                cnt += 1
            i += 1
    if restart is True:
        main = None
        previous_i = index_restart
        current_i = index_restart
        i = 0
        cnt = index_restart / progress_each
        list_metadata = []
        for index, row in files.iloc[index_restart:].iterrows():
            try:
                list_metadata.append(
                    parsers.parse_XML_metadata(
                        path=row["metadata_path"],
                        met_dir=row["metadata_dir"],
                        title=row["metadata_name"],
                        index=row["index"],
                    )
                )
            except Exception:
                # logger.debug(f"Something missing at index: {index}")
                continue
            # Each X, save the file in a .csv
            if i == save_each:
                current_i = current_i + i
                file_path = os.path.join(
                    save_path,
                    "processed_metadata_"
                    + str(previous_i)
                    + "_"
                    + str(current_i)
                    + ".csv",
                )
                main = pd.DataFrame(list(chain.from_iterable(list_metadata)))
                # main = pd.DataFrame.from_dict(dict_metadata).T.reset_index()
                main.to_csv(file_path)
                main = None
                list_metadata = []
                previous_i = current_i
                i = 0
            # Each 100 files, print the progress
            if i % progress_each == 0:
                # clear_output(wait=True)
                logger.debug("Files parsed: " + str(progress_each * cnt))
                logger.debug(
                    "Current file: "
                    + row["metadata_name"]
                    + " (Index: "
                    + str(row["index"])
                    + ")"
                )
                cnt += 1
            i += 1
