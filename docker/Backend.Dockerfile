FROM python:3.11-alpine
 
# Install system dependencies
RUN apk add --no-cache --virtual .build-deps \  
    build-base \  
    libffi-dev \  
    openssl-dev \  
    curl \
    unixodbc-dev \  
    libpq
    
# Download and install the ODBC Driver and mssql-tools
RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.6.1-1_amd64.apk \
    && curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/mssql-tools_17.10.1.1-1_amd64.apk \
    && apk add --allow-untrusted msodbcsql17_17.10.6.1-1_amd64.apk \
    && apk add --allow-untrusted mssql-tools_17.10.1.1-1_amd64.apk \
    && rm msodbcsql17_17.10.6.1-1_amd64.apk mssql-tools_17.10.1.1-1_amd64.apk

WORKDIR /app

# Copy only requirements first to leverage Docker cache
COPY ./src/Backend/requirements.txt .

# Install dependencies  
RUN pip install --no-cache-dir -r requirements.txt && rm -rf /root/.cache  

# Copy backend code
COPY ./src/Backend/ .

EXPOSE 80

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
