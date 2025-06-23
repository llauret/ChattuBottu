import wikipedia
import re
import os
from config import config

class ExternalResourceService:
    def __init__(self, youtube_api_key=None):
        """
        Initialize the external resource service.
        Args:
            youtube_api_key: API key for YouTube Data API v3 (optional)
        """
        # Set Wikipedia language to French
        wikipedia.set_lang("fr")
        
        # YouTube API setup
        self.youtube_api_key = youtube_api_key or config.YOUTUBE_API_KEY
        self.youtube = None
        if self.youtube_api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            except Exception as e:
                print(f"Warning: Could not initialize YouTube API: {e}")

    def extract_keywords(self, text, max_keywords=3):
        """
        Extract main keywords from text for searching external resources.
        This is a simple implementation - could be enhanced with NLP libraries.
        """
        # Remove common French stop words
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'ou', 'à', 'dans', 
            'pour', 'par', 'sur', 'avec', 'sans', 'sous', 'ce', 'cette', 'ces', 'est', 
            'sont', 'être', 'avoir', 'que', 'qui', 'quoi', 'comment', 'pourquoi', 'où',
            'quand', 'quel', 'quelle', 'quels', 'quelles', 'c\'est', 'il', 'elle', 'ils',
            'elles', 'nous', 'vous', 'me', 'te', 'se', 'ma', 'ta', 'sa', 'mon', 'ton', 'son'
        }
        
        # Clean and split text
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', text.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Return unique keywords, limited by max_keywords
        return list(dict.fromkeys(keywords))[:max_keywords]

    def search_wikipedia(self, query, max_sentences=3):
        """
        Search Wikipedia for information about the query.
        Returns a dictionary with title, summary, and URL.
        """
        try:
            # Search for the most relevant page
            search_results = wikipedia.search(query, results=3)
            if not search_results:
                return None
            
            # Try to get the page content
            for title in search_results:
                try:
                    page = wikipedia.page(title)
                    # Get a short summary
                    summary = wikipedia.summary(title, sentences=max_sentences)
                    
                    return {
                        'title': page.title,
                        'summary': summary,
                        'url': page.url,
                        'source': 'Wikipedia'
                    }
                except wikipedia.exceptions.DisambiguationError as e:
                    # Try the first option in case of disambiguation
                    try:
                        page = wikipedia.page(e.options[0])
                        summary = wikipedia.summary(e.options[0], sentences=max_sentences)
                        return {
                            'title': page.title,
                            'summary': summary,
                            'url': page.url,
                            'source': 'Wikipedia'
                        }
                    except:
                        continue
                except:
                    continue
            
            return None
            
        except Exception as e:
            print(f"Error searching Wikipedia: {e}")
            return None

    def search_youtube_videos(self, query, max_results=3):
        """
        Search YouTube for educational videos related to the query.
        Returns a list of video dictionaries with title, URL, and channel.
        """
        if not self.youtube:
            return []
        
        try:
            # Search for videos
            search_response = self.youtube.search().list(
                q=query + " cours tutorial explication",
                part='snippet',
                maxResults=max_results,
                type='video',
                order='relevance',
                regionCode='FR',
                relevanceLanguage='fr'
            ).execute()
            
            videos = []
            for item in search_response['items']:
                video = {
                    'title': item['snippet']['title'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'channel': item['snippet']['channelTitle'],
                    'description': item['snippet']['description'][:200] + "..." if len(item['snippet']['description']) > 200 else item['snippet']['description'],
                    'source': 'YouTube'
                }
                videos.append(video)
            
            return videos
            
        except HttpError as e:
            print(f"YouTube API error: {e}")
            return []
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return []

    def get_external_resources(self, user_question, bot_response=None):
        """
        Get external resources (Wikipedia + YouTube) based on user question.
        Returns a dictionary with Wikipedia info and YouTube videos.
        """
        # Extract keywords from the user question
        keywords = self.extract_keywords(user_question)
        if not keywords:
            return {'wikipedia': None, 'youtube': []}
        
        # Use the first few keywords for searching
        search_query = ' '.join(keywords[:2])
        
        # Search Wikipedia
        wikipedia_info = self.search_wikipedia(search_query)
        
        # Search YouTube
        youtube_videos = self.search_youtube_videos(search_query)
        
        return {
            'wikipedia': wikipedia_info,
            'youtube': youtube_videos,
            'keywords_used': keywords[:2]
        }

    def format_external_resources_html(self, resources):
        """
        Format external resources as HTML for display in the chat.
        """
        if not resources or (not resources.get('wikipedia') and not resources.get('youtube')):
            return ""
        
        html = '<div class="external-resources">'
        html += '<h4><span class="material-icons">public</span> Ressources complémentaires</h4>'
        
        # Wikipedia section
        if resources.get('wikipedia'):
            wiki = resources['wikipedia']
            html += f'''
            <div class="resource-item wikipedia-resource">
                <div class="resource-header">
                    <span class="material-icons">article</span>
                    <strong>{wiki['title']}</strong>
                    <span class="resource-source">Wikipedia</span>
                </div>
                <p class="resource-summary">{wiki['summary']}</p>
                <a href="{wiki['url']}" target="_blank" class="resource-link">
                    Lire l'article complet <span class="material-icons">open_in_new</span>
                </a>
            </div>
            '''
        
        # YouTube section
        if resources.get('youtube'):
            html += '<div class="youtube-resources">'
            html += '<h5><span class="material-icons">play_circle</span> Vidéos explicatives</h5>'
            for video in resources['youtube']:
                html += f'''
                <div class="resource-item youtube-resource">
                    <div class="resource-header">
                        <span class="material-icons">play_arrow</span>
                        <strong>{video['title']}</strong>
                    </div>
                    <p class="resource-channel">Par {video['channel']}</p>
                    <a href="{video['url']}" target="_blank" class="resource-link youtube-link">
                        Regarder sur YouTube <span class="material-icons">open_in_new</span>
                    </a>
                </div>
                '''
            html += '</div>'
        
        html += '</div>'
        return html
