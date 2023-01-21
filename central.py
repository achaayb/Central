#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey, sleep, spawn

# Gevent monkeypatch
monkey.patch_all()

import json
import logging
import sqlite3
from datetime import datetime

import requests
import yaml
from requests.exceptions import RequestException

from bottle import (HTTPResponse, auth_basic, get, post, request, run,
                    static_file)

logger = logging.getLogger("Central")

conn = sqlite3.connect("db.sqlite")
config = yaml.safe_load(open("config.yaml"))

APPLICATIONS = config["applications"]
API_KEYS = {}
for application in APPLICATIONS:
    API_KEYS[application["apiKey"]] = application["scope"]

USERNAME = config["credentials"]["username"]
PASSWORD = config["credentials"]["password"]
DISCORD_ENABLED = config["discord"]["discordEnabled"]
DISCORD_HOOK = config["discord"]["discordHook"]
LOGS_TABLE_NAME = "Logs"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
DATETIME_FORNAT = "%Y-%m-%d"

def is_authenticated_user(user, password):
    """Basic http authentication check function.
    
    :param user: username
    :param password: password
    :returns: True if valid username and password else False
    """
    if user == USERNAME and password == PASSWORD:
        return True
    return False

@get("/dashboard")
def dashboard():
    """Static dashboard page.
    
    :returns: static file
    """
    return static_file("dashboard.html", root="static")

def insert_log(
    level: str = "UNDEFINED", scope: str = "scopeless", message: str = "blank"
):
    """Inserts a log in the database.
    
    :param level: level or severity of the log
    :param scope: log scope or application name
    :param message: log message
    """
    stmt = """INSERT INTO {0}
    (level, scope, message, timestamp)
    VALUES (?, ?, ? ,?)"""
    conn.execute(
        stmt.format(LOGS_TABLE_NAME),
        (level, scope, message, datetime.now().strftime(TIMESTAMP_FORMAT)),
    )
    conn.commit()
    if DISCORD_ENABLED:
        requests.post(
            DISCORD_HOOK,
            json={
                "embeds": [
                    {
                        "title": scope,
                        "description": message,
                        "color": 16777215,
                        "footer": {"text": "Log level: {0}".format(level)},
                        "timestamp": datetime.now().strftime(TIMESTAMP_FORMAT),
                    }
                ]
            },
        )

def count_total_logs():
    """Counts total rows.
    
    :returns: rows count
    """
    cur = conn.cursor()
    stmt = "SELECT count(id) as total FROM {0}".format(LOGS_TABLE_NAME)
    cur.execute(stmt)
    result = cur.fetchone()
    return result[0]

def paginate_logs(offset: int, elements_per_page: int):
    """Paginates logs.
    
    :param offset: pagination offset
    :param selements_per_page: elements per page
    :returns: fetched result
    """
    cur = conn.cursor()
    base_stmt = (
        "SELECT id, level, scope, timestamp, message FROM {0} ORDER BY id DESC".format(
            LOGS_TABLE_NAME
        )
    )
    stmt = "{0} LIMIT {1} OFFSET {2}".format(base_stmt, elements_per_page, offset)
    cur.execute(stmt)
    query_result = cur.fetchall()
    result = {}
    result["data"] = query_result
    result["recordsFiltered"] = len(query_result)
    result["recordsTotal"] = count_total_logs()
    return result

@get("/api/logs")
@auth_basic(is_authenticated_user)
def get_logs():
    """Get paginated logs and return json result.
    
    :returns: paginated result in json format
    """
    offset = int(request.query["start"])
    length = int(request.query["length"])
    logs = paginate_logs(offset, length)
    return json.dumps(logs)


@post("/api/logs")
def create_log():
    """Create log function.
        
    :returns: request_body
    """
    api_key = request.get_header("Authorization")
    scope = API_KEYS.get(api_key, None)
    if not scope:
        return HTTPResponse(status=401, body="Unauthorized")
    request_body = request.json
    level = request_body.get("level", "Undefined")
    message = request_body.get("message", "Undefined")
    insert_log(
        level,
        scope,
        message,
    )
    logger.info("Created log on scope {0}".format(scope))
    return request_body


def health_check(
    scope: str,
    endpoint: str,
    frequency: int,
    timeout: int,
):
    """Health check loop function.
    
    :param scope: Scope string
    :param endpoint: Endpoint returning 200
    :param frequency: Frequency of the health check in seconds
    :param timeout: Seconds to wait to consider the endpoint offline 
    """
    while not sleep(frequency):
        try:
            response = requests.get(endpoint, timeout=timeout)
            if response.status_code != 200:
                raise RequestException("response code != 200")
            logger.info(
                "Health check {0} on endpoint {1} success".format(scope, endpoint)
            )
        except RequestException:
            logger.info(
                "Health check {0} on endpoint {1} failed".format(scope, endpoint)
            )
            message = "Health check timeout after {0}s on endpoint {1}".format(
                timeout, endpoint
            )
            insert_log("CRITICAL", scope, message)


@get("/ping")
def ping():
    """Health check endpoint.
    
    :returns: HTTPResponse
    """
    return HTTPResponse(status=200, body="pong")

if __name__ == "__main__":
    # Loop on all applications in config file and spawn
    # a health check greenlet that pings the health check
    # endpoint every frequency in seconds
    for application in APPLICATIONS:
        if application["healthCheckEnabled"] is True:
            scope = application["scope"]
            endpoint = application["healthCheckEndpoint"]
            frequency = application["healthCheckFrequency"]
            timeout = application["healthCheckTimeout"]
            spawn(
                health_check,
                scope,
                endpoint,
                frequency,
                timeout,
            )
    run(server="gevent", host="0.0.0.0", port=8099, debug=False, reloader=False)