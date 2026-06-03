import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import urlparse

def extract_job_description_from_url(job_url: str) -> dict:
    if not job_url or not job_url.strip().startswith(("http://", "https://")):
        return {
            "success": False,
            "source_url": job_url,
            "extracted_text": "",
            "message": "Could not extract job description from this URL. Please paste the job description manually."
        }

    job_url = job_url.strip()
    parsed_url = urlparse(job_url)
    domain = parsed_url.netloc.lower()
    is_linkedin = "linkedin.com" in domain

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
    }

    try:
        if is_linkedin:
            # Handle LinkedIn gracefully as requested
            try:
                response = requests.get(job_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    # Try common selectors for public LinkedIn postings
                    desc_element = (
                        soup.select_one(".show-more-less-html__markup") or
                        soup.select_one(".description__text") or
                        soup.select_one(".jobs-description__content") or
                        soup.select_one(".job-description") or
                        soup.select_one("section.description")
                    )
                    if desc_element:
                        text = desc_element.get_text(separator="\n").strip()
                        if text:
                            return {
                                "success": True,
                                "source_url": job_url,
                                "extracted_text": text,
                                "message": "Job description extracted successfully."
                            }
            except Exception:
                pass

            # Try trafilatura fallback for LinkedIn
            try:
                downloaded = trafilatura.fetch_url(job_url)
                if downloaded:
                    text = trafilatura.extract(downloaded)
                    if text and len(text.strip()) > 100:
                        return {
                            "success": True,
                            "source_url": job_url,
                            "extracted_text": text.strip(),
                            "message": "Job description extracted successfully."
                        }
            except Exception:
                pass

            # Failure fallback for LinkedIn
            return {
                "success": False,
                "source_url": job_url,
                "extracted_text": "",
                "message": "Could not extract job description from this URL. Please paste the job description manually."
            }

        # For non-LinkedIn URLs, try trafilatura first as it removes boilerplates nicely
        try:
            downloaded = trafilatura.fetch_url(job_url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                if text and len(text.strip()) > 100:
                    return {
                        "success": True,
                        "source_url": job_url,
                        "extracted_text": text.strip(),
                        "message": "Job description extracted successfully."
                    }
        except Exception:
            pass

        # BeautifulSoup fallback for generic site
        try:
            response = requests.get(job_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Remove common non-content elements
                for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    element.decompose()
                
                # Try finding common article/content wrappers, fallback to body
                content_area = soup.find("main") or soup.find("article") or soup.find("body")
                if content_area:
                    text = content_area.get_text(separator="\n").strip()
                    lines = [line.strip() for line in text.splitlines()]
                    clean_text = "\n".join(l for l in lines if l)
                    if len(clean_text) > 100:
                        return {
                            "success": True,
                            "source_url": job_url,
                            "extracted_text": clean_text,
                            "message": "Job description extracted successfully."
                        }
        except Exception:
            pass

        return {
            "success": False,
            "source_url": job_url,
            "extracted_text": "",
            "message": "Could not extract job description from this URL. Please paste the job description manually."
        }

    except Exception:
        return {
            "success": False,
            "source_url": job_url,
            "extracted_text": "",
            "message": "Could not extract job description from this URL. Please paste the job description manually."
        }
