# Terra helper
Terra helper is a collection of scripts which leverage the [Terra API](https://api.firecloud.org) and [gsutil]() to perform cumbersome tasks on [Terra](https://app.terra.bio/#workspaces). A more appropriate name for this repository may be `Terra storage helper`, as the scripts pretty much just deal with cleaning up workspaces or moving underlying buckets. The python package [fiss](https://github.com/broadinstitute/fiss) also has a function called mop which tries to clean up intermediate files. 

Navigate to the [`terra-helper`](terra-helper/) folder for individual scripts and corresponding documentation. For use cases, refer to the [docs](docs) folder. Current use cases documented include,
- [Manually cleaning a workspace](docs/manually-cleaning-a-workspace.md)
- [Moving a bucket](docs/moving-a-bucket.md)

## Installation

### System requirements
To use terra storage helper, you must have the following set up on your system
- [Google Cloud SDK](https://cloud.google.com/storage/docs/gsutil_install)
- Python 3

Google Cloud and Terra use [Google Cloud SDK](https://cloud.google.com/storage/docs/gsutil_install) to manage authentication. The [application default credentials](https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login) will be used. **Please walk through Google's wonderful install and set up documentation if you have not**. To login and set an application default, make sure that you've run the following,
```bash
gcloud auth login
gcloud auth application-default login
```

You may need to export your google cloud auth token, add this to your bash profile:
```bash
export GCS_OAUTH_TOKEN=`gcloud auth application-default print-access-token`
```

### Download this software from Github
This package can be downloaded through Github on the website or by using terminal. To download on the website, navigate to the top of this page, click the green `Clone or download` button, and select `Download ZIP`. This will download this repository in a compressed format. To install using Github on terminal, type 

```bash
git clone https://github.com/vanallenlab/terra-helper.git
cd terra-helper
```

### Install Python dependencies
Terra helper uses Python 3.10. We recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) and running Python with either [Anaconda](https://www.anaconda.com/download/) or  [Miniconda](https://conda.io/miniconda.html). 

To create a virtual environment and install dependencies with Anaconda or Miniconda, run the following from this repository's directory:
```bash
conda create -y -n terra-helper python=3.10
conda activate terra-helper
pip install -r requirements.txt
```

If you are using base Python, you can create a virtual environment and install dependencies by running:
```bash
virtualenv terra-helper
source activate terra-helper/bin/activate
pip install -r requirements.txt
```
