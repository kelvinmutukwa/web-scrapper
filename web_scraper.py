import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_safe_output_path():
    """Get a safe output path that we have permission to write to"""
    # Try project directory first
    project_dir = Path(__file__).parent
    output_path = project_dir / 'scraped_data.csv'
    
    # If we can't write to project dir, use Documents
    if not os.access(project_dir, os.W_OK):
        documents_dir = Path.home() / 'Documents'
        output_path = documents_dir / 'vacancymail_scraped_data.csv'
        
    return output_path

def scrape_vacancymail():
    """Scrape job listings from VacancyMail and save to CSV"""
    url = "https://vacancymail.co.zw/jobs/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logging.info(f"Starting scrape of {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        job_listings = soup.find_all('a', class_='job-listing')
        
        jobs_data = []
        for job in job_listings[:10]:  # Get first 10 jobs
            try:
                title = job.find('h3', class_='job-listing-title').text.strip()
                company = job.find('h4', class_='job-listing-company').text.strip() if job.find('h4', class_='job-listing-company') else "Not specified"
                description = job.find('p', class_='job-listing-text').text.strip() if job.find('p', class_='job-listing-text') else "No description"
                
                # Extract location and expiry date from footer
                footer = job.find('div', class_='job-listing-footer')
                location = expiry = "Not specified"
                if footer:
                    items = footer.find_all('li')
                    for item in items:
                        if 'icon-material-outline-location-on' in str(item):
                            location = item.text.strip()
                        elif 'icon-material-outline-access-time' in str(item) and 'Expires' in str(item):
                            expiry = item.text.replace('Expires', '').strip()
                
                jobs_data.append({
                    'Job Title': title,
                    'Company': company,
                    'Location': location,
                    'Expiry Date': expiry,
                    'Description': description,
                    'Scraped Date': datetime.now().strftime('%Y-%m-%d')
                })
                
            except Exception as e:
                logging.warning(f"Error processing job listing: {e}")
                continue
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(jobs_data)
        output_path = get_safe_output_path()
        
        try:
            df.to_csv(output_path, index=False)
            logging.info(f"Successfully saved {len(jobs_data)} jobs to {output_path}")
            print(f"Data saved to: {output_path}")
        except PermissionError:
            logging.error(f"Permission denied for {output_path}")
            raise
        except Exception as e:
            logging.error(f"Error saving file: {e}")
            raise
        
        return df
        
    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        raise

if __name__ == "__main__":
    scrape_vacancymail()