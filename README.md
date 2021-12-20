# Usage

## Docker

```
docker run -it --rm madwaks/crypto-downloader:latest <command> {args}
```
### Available commands

#### Import quotes from a coin and a time unit

To download quotes from ETH/BTC, run the following:

```
docker run -it --rm madwaks/crypto-downloader:latest importquotes --symbol=ETHBTC --time-unit=4h
```

#### Import all available symbols

```
docker run -it --rm madwaks/crypto-downloader:latest importsymbols
```

### Bind a volume

You will need to bind a folder to `/data`. Choose a folder on your local machine and add it to docker run arguments:
```
docker run -it --rm -v /path/to/your/folder/data/:/data madwaks/crypto-downloader:latest <command> {args}
```
