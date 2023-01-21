# Central

Central is a highly efficient, lightweight application that facilitates the collection of logs from various sources, as well as the monitoring of their health status. Utilizing bottle.py and gevent technologies, Central is designed to offer a seamless user experience while maintaining high performance standards.

## Installation

To begin using Central, please follow the steps outlined below:

1. Obtain the source code by executing the command `git clone https://github.com/achaayb/Central.git` in your terminal.
2. Install the necessary dependencies by running `pip install gevent`.
3. Configure the application by editing the `config.yaml` file.
4. Launch the application by executing the command `python central.py`.

## Main endpoint

- The main endpoint to insert logs is `/api/logs`, Make sure to append the Authorization Header with the api key set in the config.yaml
- Example request body: 

```
{
    "level": "DEBUG",
    "message": "Debug message"
}
```

## Usage

Upon successful launch, the Central web interface can be accessed by navigating to `http://localhost:8099` in your web browser. The interface allows for the configuration of the applications to be monitored, setup of notifications through Discord, and real-time viewing of collected logs.

![Central Flow](/static/flow.jpg)

## Features

- Multi-source log collection
- Health status monitoring for applications
- Discord-based notifications for alerts
- Intuitive web interface
- Flexible configuration options via `config.yaml` file

## Contribution

The Central community welcomes contributions in the form of pull requests, bug reports, and feature suggestions. Together, we can continue to improve Central and make it the premier log collection and monitoring solution.

## License

Central is released under the MIT License. For further information, please refer to the [LICENSE](https://github.com/achaayb/Central/blob/master/LICENSE) file.