import os
from venv import create

class NodeEnvExtractor:
    envFound = set()
    projectName = ""
    rootDir = ""

    def __init__(self, rootDir):
        self.rootDir = rootDir
        self.setProjectName()
        print("Generating deployment snippet for env variables.")
        self.generateEnvSnippet()
        print("Generated Snippets, Saved in file: " + self.projectName + ".yml")
        print("Do you want to generate akvs objects as well? (Y/N)")
        res = input()
        if res == 'Y' or res == 'y':
            print("Enter the Namespace: ")
            namespace = input()
            print("Enter the AKV Name: ")
            akv = input()
            self.generateAKVSSnippet(namespace, akv)
            print("Generated AKVS Objects, Saved in file: akvs.yml")
        
    def generateEnvSnippet(self):
        self.findFiles()
        self.readFiles()
        print("ENV Found : " + str(self.envFound))
        self.generateEnvFile()
        os.remove("filelist.txt")

    def setProjectName(self):
        pn = self.rootDir.split('\\')
        if pn[-1] == '':
            self.projectName = pn[-2]
        else:
            self.projectName = pn[-1]

    def findFiles(self):
        with open("filelist.txt", 'w') as f:
            for current_path, directories, files in os.walk(self.rootDir):
                if "node_modules" in current_path:
                    continue
                for file in files:
                    if os.path.splitext(file)[1] == ".js" or os.path.splitext(file)[1] == ".ts" or os.path.splitext(file)[1] == ".tsx":
                        f.write(os.path.join(current_path, file))
                        f.write('\n')

    def readFiles(self):
        with open("filelist.txt", 'r') as f:
            file = f.readline()
            while(len(file) > 0):
                self.parseFile(file)
                file = f.readline()

    def parseFile(self, file):
        file = file[0:len(file) - 1]
        with open(file, 'r') as f:
            line = f.readline()
            while(len(line) > 0):
                if "process.env" in line:
                    env = self.extractEnv(line)
                    self.envFound.add(env)
                line = f.readline()

    def extractEnv(self, line):
        line = line[line.index("process.env") + len("process.env.")::]
        i = 0
        for i in range(len(line)):
            if not (line[i].isalnum() or line[i] == '_'):
                break
        return line[0:i:]

    def generateEnvFile(self):
        for env in self.envFound:
            if env != "":
                with open(f'./{self.projectName}.yml', 'a') as f:
                    f.write("- name: " + env)
                    f.write('\n')
                    f.write("  value: " + self.projectName.lower() + "-" + self.getEnvAKVSObjName(env) + "@azurekeyvault")
                    f.write('\n')

    def getEnvAKVSObjName(self, env):
        env = env.lower()
        return env.replace("_", "-")

    def createAKVSObj(self, akvObjName, namespace, akvName):
        with open("./akvs.yml", 'a') as f:
            AKVSobj = f'''
apiVersion: spv.no/v2beta1
kind: AzureKeyVaultSecret
metadata:
  name: {akvObjName}
  namespace: {namespace}
spec:
  vault:
    name: {akvName}
    object:
      name: {akvObjName.upper()}
      type: secret
---'''
            f.write(AKVSobj)

    def generateAKVSSnippet(self, namespace, akv):
        self.namespace = namespace
        self.akv = akv
        for env in self.envFound:
            if env != "":
                self.createAKVSObj(self.projectName.lower() + "-" + self.getEnvAKVSObjName(env), \
                    self.namespace, self.akv)