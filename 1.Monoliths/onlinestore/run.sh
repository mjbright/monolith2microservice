
[ -f ~/.venv/flask/bin/activate ] && source  ~/.venv/flask/bin/activate

[ -z "$1" ] && set -- 5000

python3 app.py $1

