FROM python:alpine3.21

RUN apk add --no-cache ffmpeg==6.1.2-r1

RUN apk add --no-cache aria2 \
	&& adduser -D aria2 \
	&& mkdir -p /etc/aria2 \
	&& mkdir -p /aria2down \
	&& rm -rf /var/lib/apk/lists/*

RUN apk add --no-cache \
  tzdata \
  jq  \
  exiv2  \
  bash  \
  curl  \
  perl  \
  coreutils \
  grep \
  deno

RUN pip install --no-cache-dir bottle yt-dlp-ejs yq
RUN pip install https://github.com/stradus64/chat-downloader/archive/refs/heads/fix_issue_271.zip

WORKDIR /usr/local/bin/

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY live-dl autoscript.sh youtube-dl-server.py index.html /usr/src/app/
COPY /config /usr/src/app/config
COPY /static /usr/src/app/static
RUN chmod a+x /usr/src/app/live-dl \
	&& chmod +x /usr/src/app/autoscript.sh \
	&& chmod +x /usr/src/app/config/
RUN ln -s /usr/src/app/live-dl /usr/local/bin/live-dl && \
	ln -s /usr/src/app/config /usr/local/bin/config

EXPOSE 8080

VOLUME ["/youtube-dl"]

CMD [ "/usr/src/app/autoscript.sh" ]
