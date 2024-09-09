FROM python:3.11
RUN mkdir -p /app

# 3. Copy the application files into the working directory
COPY requirements.txt .

# 4. Install any dependencies (for Node.js apps, it's usually npm install)
RUN RUN pip install --no-cache-dir -r requirements.txt


# 5. Copy the current directory contents into the container
COPY . .

# 6. Set environment variables (optional)
ENV FLASK_APP=app.py
ENV FLASK_ENV=production  


# 7. Expose the port that Flask will run on
EXPOSE 5000

# 8. Run the application
CMD ["flask", "run", "--host=0.0.0.0"]