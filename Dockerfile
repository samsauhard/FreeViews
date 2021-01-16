FROM python:3

ENV HOME /root
WORKDIR $HOME
# Create and change to the app directory
COPY . .
# Copy application dependency manifests to the container image.
# A wildcard is used to ensure both package.json AND package-lock.json are copied.
# Copying this separately prevents re-running npm install on every code change.

RUN apt-get update && apt-get install -y \
	apt-transport-https \
	ca-certificates \
	curl \
	gnupg \
	--no-install-recommends \
	&& curl -sSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
	&& echo "deb https://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
	&& apt-get update && apt-get install -y \


# Install dependencies.
RUN pip install -r requirements.txt
#RUN apt-get install -y chromium-browser

# Install chromedriver for Chromium
# Copy local code to the container image.


# Run the web service on container startup.
CMD [ "python", "viewbot.py" ]
