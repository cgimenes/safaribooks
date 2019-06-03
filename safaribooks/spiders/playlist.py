import scrapy
import json


class PlaylistSpider(scrapy.spiders.Spider):
    name = 'SafariBooksPlaylist'
    start_urls = ['https://www.safaribooksonline.com/']
    host = 'https://www.safaribooksonline.com/'
    playlist_url = 'https://www.safaribooksonline.com/api/v2/collections/'
    metadata_url = 'https://www.safaribooksonline.com/api/v1/metadata/'

    def __init__(
        self,
        user,
        password,
        cookie,
        playlistid
    ):
        self.user = user
        self.password = password
        self.cookie = cookie
        self.playlistid = str(playlistid)


    def parse(self, response):
        if self.cookie is not None:
            cookies = dict(x.strip().split('=') for x in self.cookie.split(';'))

            return scrapy.Request(url=self.host + 'home',
                callback=self.after_login,
                cookies=cookies,
                headers={
                    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'
                })

        return scrapy.FormRequest.from_response(
              response,
              formdata={'email': self.user, 'password1': self.password},
              callback=self.after_login
        )


    def after_login(self, response):
        # Loose rule to decide if user signed in successfully.
        if response.status == 401:
            self.logger.error('Failed login')
            return
        elif response.status != 200:
            self.logger.error('Something went wrong')
            return
        yield scrapy.Request(
            self.playlist_url + self.playlistid,
            callback=self.get_books_metadata,
        )


    def get_books_metadata(self, response):
        if response.status != 200:
            self.logger.error('Something went wrong')
            return
        jsonresponse = json.loads(response.body_as_unicode())
        books = list(map(lambda x: str(x['api_url']), jsonresponse['content']))
        payload = json.dumps({'urls': books})

        yield scrapy.Request(
            self.metadata_url,
            method='POST',
            body=payload,
            headers={'Content-Type':'application/json'},
            callback=self.get_books_id
        )


    def get_books_id(self, response):
        if response.status != 200:
            self.logger.error('Something went wrong')
            return
        jsonresponse = json.loads(response.body_as_unicode())
        for book in jsonresponse:
            yield {'id': str(book['identifier'])}
