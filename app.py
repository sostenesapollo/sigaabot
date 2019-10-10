from flask import Flask, request
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)
CORS(app)
session = requests.Session()

url = {
	'login':'https://sigaa.ufpi.br/sigaa/logar.do?dispatch=logOn',
	'turma':'https://sigaa.ufpi.br/sigaa/ufpi/portais/discente/discente.jsf'								  
}
h = {
	"Upgrade-Insecure-Requests" : "1"
}

@app.route("/")
def main():
	user = {'user.login':'sostenesapollo12','user.senha':'81020002abc'}
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

	print(data['disciplinas'][0]['form'])
	turma_request = session.post(url['turma'], params=data['disciplinas'][0]['form'])
	turma_soup = BeautifulSoup(turma_request.text,'html.parser')

	s = turma_soup.find(id='formAva').find_all('span')
	
	f = open("file.html",'w')	
	for i in s:
		if i.find(class_='titulo'):
			title = i.find(class_='titulo').text.replace("\n",'').replace("\t",'')
			print(title)
		if i.find(class_='conteudotopico'):			
			content = i.find(class_='conteudotopico').find_all('span')
			if(len(content) > 0):
				for span in content:
					if(span.find('a')):
						print('--->',span.find('a').text)

		f.write(str(i))
		f.write("\n\n*****************\n\n")
	f.close()
	return(turma_request.text)

main()

if __name__  == "__main__" :	
	app.run(debug = True)