import http.server
import socketserver
import threading
import glob
import json
import re
import tempfile
import webbrowser
import os
from functools import partial
import signal
import sys

from time import sleep
from pathlib import Path
from functools import partial

# NOTE: Fix '/' and '\' pathing for multi os support
# NOTE: Improve pathing
# TODO: Improve logging
# TODO: Improve errors; check if we have the correct files to operate in.
# Verify stuff like module.json, module-style.css etc...

# TODO: Make class for hadeling module information; don't let the thing that gets
# styles be the same that gets module info!
# TODO: Add page titles
# TODO: Basic support for page padding and better bg colors


class TCPServerReuse(socketserver.TCPServer):
    allow_reuse_address = True

class Browser:
    def __init__(self, htmlContent, styleSheet, address, moduleId) -> None:
        self.styleSheet = styleSheet
        self.address = address
        self.deleteTemp = True
        self.port = 1200

        self.genTemp = self.makeTempFiles(
            htmlContent,
            styleSheet,
            moduleId
        )

        handler = partial(http.server.SimpleHTTPRequestHandler, directory=self.address)
        self.httpd = TCPServerReuse(("", self.port), handler)

        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        webbrowser.open(f"http://localhost:{self.port}/{os.path.basename(self.genTemp['html'])}")

        print(f"Serving on http://localhost:{self.port}/ (Press Ctrl+C to stop)")

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.pause()


    def signal_handler(self, signum, frame):
        print("\nShutting down server...")
        self.cleanTemp(self, self.genTemp)
        self.httpd.shutdown()
        self.httpd.server_close()
        sys.exit(0)


    def makeTempFiles(self, htmlContent, styleSheet, moduleId):
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.css', dir=self.address) as f:
            tempStyleRef = f.name
            f.write(styleSheet)

        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', dir=self.address) as f:
            tempHtmlContent = f.name
            f.write(self.packHtml(htmlContent, os.path.relpath(tempStyleRef, self.address), moduleId))

        files = {
            "html": tempHtmlContent,
            "css": tempStyleRef
        }

        print(files['css'])

        return files


    def packHtml(self, pages, styleSheet, moduleId) -> str:
        pages = pages.replace(f'src="modules/{moduleId}/', 'src="')
        pages = pages.replace(f'src="/modules/{moduleId}/', 'src="')
        pages = pages.replace(f'url(modules/{moduleId}/', 'url(')

        final = f"""
        <html>
        <head>
            <title>{moduleId}</title>
            <link rel="stylesheet" href="{styleSheet}">
        </head>
        <body >
            <div class="jvis-wrapper">
                {pages}
            </div>
        </body>
        </html>
        """
        return final
    
    @classmethod
    def cleanTemp(cls, self, cleanTargets) -> None:
        if self.deleteTemp:
            for f in cleanTargets.values():
                os.remove(f)

            print("Cleaned temp files!")
        pass


class IO:
    def __init__(self) -> None:
        self.cwd = os.getcwd()
        self.absolutePath = Path(__file__).resolve().parent

        self.journalPath = os.path.join(self.cwd, "src", "packs", "**", "*.json")
        self.moduleInfo = os.path.join(self.cwd, "module.json")

        self.baseCss = os.path.join(self.absolutePath, "css/base.css")
        self.cssRef = self.getStyleRef()

        pass

    def getSourceJournals(self) -> list[str]:
        journals = glob.glob(self.journalPath, recursive=True)
        journals = [x for x in journals if x.split('/')[-1].startswith('journal_')]

        return journals
    
    def getStyleRef(self) -> str:
        with open(self.moduleInfo, 'r', encoding='utf-8') as module:
            cssRef = json.loads(module.read())
            
            # NOTE: Please fix this future deludank
            self.moduleId = cssRef['id'] 
            # NOTE: pray that we have only one style per module
            cssRef = cssRef['styles'][0] 

        return cssRef

    def getStyleRefContent(self) -> str:
        print(self.baseCss)
        with open(self.baseCss, 'r', encoding='utf-8') as baseCss:
            baseCssRef = baseCss.read()

        with open(self.cssRef, 'r', encoding='utf-8') as css:
            cssRef = css.read()
            # TODO: Fix this please
            cssRef = cssRef.replace('../', '')
            cssRef = baseCssRef + cssRef

        return cssRef


class JournalVis:
    def __init__(self, sourcePaths) -> None:
        self.sourcePaths = sourcePaths
        self.sourceFiles = list()
        self.allPages = list()

        for f in sourcePaths:
            with open(f, 'r', encoding='utf-8') as fs:
                newDict = json.loads(fs.read())
                self.sourceFiles.append(newDict)

        self.sortedFiles = self.sortElements(self.sourceFiles)

        pass


    def removeEnrichers(self, content):
        # final = content
        final = re.sub(r'@UUID\[.*?\]\{(.*?)\}', r'<a class="content-link">\1</a>', content)
        # final = re.sub(r'\[\[/r\s(.*?)\]\]', r'<a class="inline-roll roll">\1</a>', content)
        return final

    def sortElements(self, elements: list[dict]) -> list[dict]:
        """Sort elements of list of dicts by value of 'sort' key."""
        return sorted(elements, key=lambda x: x['sort'])

    def getPages(self) -> str:
        for f in self.sortedFiles:
            self.allPages.extend(f['pages'])
        
        # NOTE: not great. but fuck you LMAO GOTTEM.
        oTag = '<div class="sheet journal-entry"> <section class="journal-entry-content"> <div class="journal-entry-pages"> <article> <section class="journal-page-content">'
        cTag = '</section> </article> </div> </section> </div>'
        self.allPages = [oTag + x['text']['content'] + cTag for x in self.allPages]

        final = ''.join(self.allPages)
        final = self.removeEnrichers(final) 

        # TODO: fix this join asap
        return final

        

src = IO()
vis = JournalVis(src.getSourceJournals())
Browser(vis.getPages(), src.getStyleRefContent(), src.cwd, src.moduleId)
