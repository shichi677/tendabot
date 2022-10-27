# from modules import get_spec_from_wiki_MS_page
from modules import clanmatch_schedule

# print(GFW.get_MS_page_url_from_wiki())
# URL = "https://w.atwiki.jp/battle-operation2/pages/121.html"
# print(get_spec_from_wiki_MS_page(URL))
clanmatch_info = clanmatch_schedule()
print(clanmatch_info)
