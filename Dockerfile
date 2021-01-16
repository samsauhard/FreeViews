FROM python:3

ENV HOME /root
WORKDIR $HOME
# Create and change to the app directory
COPY . .
# Copy application dependency manifests to the container image.
# A wildcard is used to ensure both package.json AND package-lock.json are copied.
# Copying this separately prevents re-running npm install on every code change.

RUN apt-get update
RUN apt-get install -y gconf-service libasound2 libatk1.0-0 libcairo2 libcups2 libfontconfig1 libgdk-pixbuf2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libxss1 fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install


# Install dependencies.
RUN pip install -r requirements.txt
#RUN apt-get install -y chromium-browser

# Install chromedriver for Chromium
RUN curl https://chromedriver.storage.googleapis.com/75.0.3770.140/chromedriver_linux64.zip -o /usr/local/bin/chromedriver.zip
RUN unzip /usr/local/bin/chromedriver.zip -d /usr/local/bin/
RUN chmod +x /usr/local/bin/chromedriver || rm /usr/local/bin/chromedriver.zip
# Copy local code to the container image.


# Run the web service on container startup.
CMD [ "python", "viewbot.py" ]
