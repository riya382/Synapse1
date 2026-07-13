from git import Repo
from langchain.document_loaders import GitLoader
import os
import shutil
import stat
from dotenv import load_dotenv

load_dotenv()

def file_filter(file_path):
    ignore_filepaths = ["package-lock.json"]
    for ignore_filepath in ignore_filepaths:
        if ignore_filepath in file_path:
            return False
    return True

def _remove_readonly(func, path, exc_info):
    # Windows marks files inside .git (objects/pack/*.idx, *.pack) as
    # read-only, so rmtree's default unlink fails with PermissionError.
    # Clear the read-only bit and retry the operation that failed.
    os.chmod(path, stat.S_IWRITE)
    func(path)

class GithubLoader:
    def __init__(self):
        pass

    def load(self, url: str):
        tmp_path = os.path.join(os.environ.get("TEMP", "/tmp"), "github_repo")
        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path, onerror=_remove_readonly)
        repo = Repo.clone_from(url, to_path=tmp_path)
        repo.close()  # release file handles before any later cleanup
        branch = repo.head.reference
        loader = GitLoader(repo_path=tmp_path, branch=branch, file_filter=file_filter)
        return loader