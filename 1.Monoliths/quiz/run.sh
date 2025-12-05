
cd $( dirname $0 )

[ -f ~/.venv/mkdocs/bin/activate ] && source ~/.venv/mkdocs/bin/activate
[ -f ~/.venv/flask/bin/activate  ] && source ~/.venv/flask/bin/activate

mv instance/quiz.db instance/quiz.db.bak
python3 -m pip install -r requirements.txt

set -x
./app.py


