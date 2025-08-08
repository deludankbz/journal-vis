import os, glob, json, webbrowser, tempfile, time

# NOTE: Fix '/' and '\' pathing for multi os support
# NOTE: Improve pathing
# TODO: Improve logging
# TODO: Improve errors; check if we have the correct files to operate in.
# Verify stuff like module.json, module-style.css etc...

# TODO: Make class for hadeling module information; don't let the thing that gets
# styles be the same that gets module info!
# TODO: Add page titles
# TODO: Basic support for page padding and better bg colors


class Browser:
    def __init__(self, htmlContent, styleSheet, address, moduleId) -> None:

        self.styleSheet = styleSheet
        self.address = address
        self.deleteTemp = False

        self.genTemp = self.makeTempFiles(
            htmlContent,
            styleSheet,
            moduleId
        )

        webbrowser.open(f"file://{self.genTemp['html']}")
        time.sleep(5)
        self.cleanTemp(self.genTemp)
        
        pass


    def makeTempFiles(self, htmlContent, styleSheet, moduleId):
        with tempfile.NamedTemporaryFile('w', delete=self.deleteTemp, suffix='.css', dir=self.address) as f:
            tempStyleRef = f.name
            f.write(styleSheet)

        with tempfile.NamedTemporaryFile('w', delete=self.deleteTemp, suffix='.html', dir=self.address) as f:
            tempHtmlContent = f.name
            f.write(self.packHtml(htmlContent, tempStyleRef, moduleId))

        files = {
            "html": tempHtmlContent,
            "css": tempStyleRef
        }
        return files


    def packHtml(self, pages, styleSheet, moduleId) -> str:
        # TODO: Replace this coriolis-tgd-core by the module id
        final = f"""
        <html>
        <head>
            <title>Test</title>
            <link rel="stylesheet" href="{styleSheet}">
            <style>
                
                .wrapper {{
                    min-width: 45rem;
                    max-width: 60rem;
                    margin: 0 auto;
                }}
            </style>
        </head>
        <body >
            <div class="wrapper">
                {pages.replace(f'src="modules/{moduleId}/', 'src="')}
            </div>
        </body>
        </html>
        """
        return final
    
    @classmethod
    def cleanTemp(cls, cleanTargets) -> None:
        for f in cleanTargets.values():
            os.remove(f)

        print("Cleaned temp files!")
        pass

class IO:
    def __init__(self) -> None:
        self.cwd = os.getcwd()
        self.journalPath = os.path.join(self.cwd, "src", "packs", "**", "*.json")
        self.moduleInfo = os.path.join(self.cwd, "module.json")

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
        with open(self.cssRef, 'r', encoding='utf-8') as css:
            cssRef = css.read()

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

    def sortElements(self, elements: list[dict]) -> list[dict]:
        """Sort elements of list of dicts by value of 'sort' key."""
        return sorted(elements, key=lambda x: x['sort'])

    def getPages(self) -> str:
        for f in self.sortedFiles:
            self.allPages.extend(f['pages'])
        
        # NOTE: not great. but fuck you LMAO GOTTEM.
        oTag = '<div class="sheet"><section class="journal-entry-content"><div class="journal-entry-pages"><article class="journal-entry-page"><section class="journal-page-content">'
        cTag = '</div></section></article></div></section>'
        self.allPages = [oTag + x['text']['content'] + cTag for x in self.allPages]


        # TODO: fix this join asap
        return ''.join(self.allPages)

        

src = IO()
vis = JournalVis(src.getSourceJournals())
Browser(vis.getPages(), src.getStyleRefContent(), src.cwd, src.moduleId)
