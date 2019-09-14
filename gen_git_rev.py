import subprocess
import os

default_output_file = os.path.join("text_game_map_maker", "git_rev.py")

def create_file(output_filename=default_output_file):
    git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()
    git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip()

    with open(output_filename, "w") as fh:
        fh.write("commit='%s'\nbranch='%s'\n" % (git_hash.decode("utf-8"),
                                                 git_branch.decode("utf-8")))

if __name__ == "__main__":
    create_file()
