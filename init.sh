pip install nltk
mkdir -p ${OPENSHIFT_DATA_DIR}nltk_data
python -m nltk.downloader -d ${OPENSHIFT_DATA_DIR}nltk_data/ wordnet
python -m nltk.downloader -d ${OPENSHIFT_DATA_DIR}nltk_data/ tagsets
python -m nltk.downloader -d ${OPENSHIFT_DATA_DIR}nltk_data/ averaged_perceptron_tagger
python -m nltk.downloader -d ${OPENSHIFT_DATA_DIR}nltk_data/ punkt

echo 在for path_ in paths:前加两行
echo OPENSHIFT_DATA_DIR = os.environ['OPENSHIFT_DATA_DIR'] + 'nltk_data'
echo paths=[OPENSHIFT_DATA_DIR]

vim ${OPENSHIFT_HOMEDIR}python/virtenv/venv/lib/python3.3/site-packages/nltk/data.py +591