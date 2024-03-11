from flask import Flask, jsonify
from mysql import connector

app = Flask(__name__)


@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    try:
        db_config = {
            'host': 'datastuntstaging.co.in',
            'user': 'u385679644_youtube_trans',
            'password': '~hHElD~U>n?2',
            'database': 'u385679644_youtube_trans'
        }

        conn = connector.connect(**db_config)
        cursor = conn.cursor()

        table_name = 'trendingtweetreplica'
        key_column = 'key'
        value_column = 'value'

        query = f'SELECT {key_column}, {value_column} FROM {table_name}'

        cursor.execute(query)

        rows = cursor.fetchall()

        result_dict = {}

        for row in rows:
            key, value = row
            result_dict[key] = value

        cursor.close()
        conn.close()

        return jsonify(result_dict)

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(port=5003)
