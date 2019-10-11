from flask import Flask, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
import re
import os

app = Flask(__name__)
CORS(app)
session = requests.Session()

url = {
	'login':'https://sigaa.ufpi.br/sigaa/logar.do?dispatch=logOn',
	'turma':'https://sigaa.ufpi.br/sigaa/ufpi/portais/discente/discente.jsf',
	'file':'https://sigaa.ufpi.br/sigaa/ava/index.jsf'										
}
h = {
	"Upgrade-Insecure-Requests" : "1",
	"Content-Type": "application/x-www-form-urlencoded"
}

def get_filename_from_cd(cd):    
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].replace('"','')

@app.route("/")
def main(user, turma_id):		
	# Extractiong info of turmas and creating forms data 
	login_request = session.post(url['login'], params=user)
	home_soup = BeautifulSoup(login_request.text, 'html.parser')
	user_board_soup = home_soup.find_all(id='agenda-docente')[1].table.find_all('tr')
	user_disciplinas_soup = home_soup.find(id='main-docente').find('tbody').find_all('tr')
	data = {"user_data":{}, "disciplinas":[]}
	# Board User Info
	for item in user_board_soup:
		if(len(item.find_all('td')) == 2):			
			data['user_data'][item.find_all('td')[0].text] = item.find_all('td')[1].text.replace("\n",'').replace('\t', ' ').replace(" ",'')
	data['Período Atual'] = home_soup.find(class_='periodo-atual').find('strong').text	
	data['img_src'] = home_soup.find(class_='foto').find('img')['src']
	# Board Disciplinas
	for i in user_disciplinas_soup:						
		disciplina = {"form":{}, "data":{}}
		if(len(i.find_all('input')) > 0):
			# Form Data
			disciplina['form'][i.find('form')['id']] = i.find('form')['id']
			disciplina['form'][i.find('form')['id']+':turmaVirtual'] = i.find('form')['id']+':turmaVirtual'
			disciplina['form']['idTurma'] = i.find_all('input')[1]['value']
			disciplina['form']['javax.faces.ViewState'] = i.find(id="javax.faces.ViewState")['value']
			# Turma Data			
			disciplina['data']['Nome'] = i.find('a').text	
			disciplina['data']['Sala'] = i.find_all('td')[1].text
			disciplina['data']['Horário'] = i.find_all('td')[2].text.replace('\t','').replace('\n','')
			data['disciplinas'].append(disciplina)			

	# print(data['disciplinas'][1]['form'])	
	turma_request = session.post(url['turma'], params=data['disciplinas'][turma_id]['form'])
	turma_soup = BeautifulSoup(turma_request.text,'html.parser')

	topicos_aulas = turma_soup.find(id='formAva').find_all(class_='topico-aula')
	files = []
	for topico in topicos_aulas:
		if not topico.find(class_='titulo') or not topico.find(class_='conteudotopico'):
			return True
		titulo =  topico.find(class_='titulo').text.replace('\n','').replace("\t",'')
		conteudo_topico = topico.find(class_='conteudotopico')
		if(len(conteudo_topico) > 0):
			conteudo_topico_texts_inside_p = conteudo_topico.find_all("p")
			conteudo_topico_files_inside_span = conteudo_topico.find_all(class_='item')
			if(len(conteudo_topico_files_inside_span) > 0):
				for file in conteudo_topico_files_inside_span:							
					f = {"post":{}}
					f["nome"] = file.find('a').text						
					f['post']["formAva"] = "formAva"
					f['post']["formAva:idTopicoSelecionado"] = turma_soup.find(id="formAva:idTopicoSelecionado")['value']
					f['post'][file.find('a')['id']] = file.find('a')['id']
					f['post']["id"] = file.find('a')['onclick'][file.find('a')['onclick'].find("'id':"):].replace("'id':'",'').split("'")[0]
					f['post']["javax.faces.ViewState"] = turma_soup.find(id="javax.faces.ViewState")['value']
					files.append(f)						
	for fl in files:		
		r = session.post(url['file'], headers=h, params=fl['post'], allow_redirects=True)
		filename = get_filename_from_cd(r.headers.get('content-disposition'))	
		foldername = data['disciplinas'][turma_id]['data']['Nome']	
		if not os.path.isdir("out/"+foldername)	:
			os.mkdir('out/'+foldername)
		if filename:			
			with open('out/'+foldername+'/'+filename , 'wb') as f:
				print("Baixando",filename)
				f.write(r.content)
	return(turma_request.text)

for i in range(0, 7):
	try:		
		main({'user.login':'sostenesapollo12','user.senha':'81020002abc'},i)
		print("---")
	except Exception as e:
		print('Exception in',str(i),str(e))	

if __name__  == "__main__" :	
	app.run(debug = True)