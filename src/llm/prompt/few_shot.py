from . import base as prompter
from src.llm.client import base as llm
from enum import Enum

NAVIGATION = """
Example 1:
Question: You have a candidate and a label. On the bases of the following heuristcs here: 
1. Strong programming skills in languages such as Python, PyTorch, and AWS/GCP are crucial for a machine learning engineer position at ElectroKare. A candidate with a strong background in programming will be able to develop and implement complex algorithms and models quickly and efficiently.
2. Good communication skills are essential for this role, as the machine learning engineer will need to collaborate with cross-functional teams, explain technical concepts to non-technical stakeholders, and present findings to senior management. A candidate with excellent communication skills will be able to effectively convey their ideas and insights to various audiences.
3. Experience in machine learning research, development, and critical thinking abilities are highly desirable for this position. A candidate with a strong background in machine learning will be able to design and implement innovative solutions that drive business growth and improve customer experiences.
4. Knowledge of cloud computing platforms such as AWS or GCP is important for this role, as the machine learning engineer will need to deploy models on these platforms and manage large datasets in a scalable manner. A candidate with experience in cloud computing will be able to leverage the power of cloud technologies to accelerate the development process and improve model performance.
5. The ability to work independently or as part of a team is crucial for success in this role, as the machine learning engineer may need to work on complex projects without direct supervision or collaborate with other engineers on large-scale initiatives. A candidate with strong independent work ethic or teamwork skills will be able to adapt quickly to new challenges and contribute meaningfully to the team's efforts." 
decide whether the following candidate: 
[{"name": "Vardhan Shorewala", "email": "vardhan@berkeley.edu", "links": ["linkedin.com/in/vardhan-shorewala-b85543172/", "github.com/vardhan-shorewala"], "phone": "510-761-1001", "educations": [{"gpa": "3.94", "degree": "Bachelors", "majors": ["Electrical Engineering", "Computer Science", "Business"], "grad_year": "2025", "institution": "University of California, Berkeley"}], "experiences": [{"skills": {"C": 1, "CI": 1, "S3": 1, "AWS": 1, "EC2": 1, "Ruby": 1, "MLOps": 1, "MySQL": 1, "React": 1, "OpenCV": 1, "Fastify": 1, "AkkaHTTP": 1, "Selenium": 1, "Solidity": 1, "AI models": 1, "CD DevOps": 1, "AWS lambda": 1, "MERN stack": 1, "TensorFlow": 1, "UiPath RPA": 1, "Material UI": 1, "Kalman filter": 1, "MetaMask Snap": 1, "AWS Cloud Stack": 1, "Machine Learning": 1, "supply-chain optimization": 1, "GAN-based machine learning models": 1, "Semaphore zero-knowledge cryptography": 1, "bipartite signal processing algorithms": 1}, "impacts": ["Improved match-rate by 35% in supply-chain optimization", "Diminished upstream API calls by 23x, saving upwards of $100,000 monthly", "Validated software architecture with SNS messages, deploying AWS Cloud Stack through CI/CD DevOps for 50K+ vendors"], "end_date": "Aug 2023", "location": "Seattle, WA", "role_title": "Software Engineering Intern", "start_date": "May 2023", "organization": "Amazon"}, {"skills": {"Ruby": 1, "MLOps": 1, "MySQL": 1, "React": 1, "Fastify": 1, "Polygon": 1, "Solidity": 1, "AI models": 1, "MERN stack": 1, "UiPath RPA": 1, "Material UI": 1, "RESTful API": 1, "MetaMask Snap": 1, "Machine Learning": 1, "L1 to L2 transactions": 1, "GAN-based machine learning models": 1, "Semaphore zero-knowledge cryptography": 1}, "impacts": ["Productionized a Voting dApp on Polygon using Solidity and Semaphore zero-knowledge cryptography", "Engineered a React-based dApp and MetaMask Snap for efficient L1 to L2 transactions without bridging contracts for Arbitrium"], "end_date": "Present", "location": "San Francisco, CA", "role_title": "Algorithm Developer", "start_date": "Jan 2023", "organization": "Blockchain at Berkeley"}, {"skills": {"C": 1, "Ruby": 1, "MLOps": 1, "MySQL": 1, "React": 1, "AkkaHTTP": 1, "AI models": 1, "MERN stack": 1, "UiPath RPA": 1, "Material UI": 1, "Machine Learning": 1, "GAN-based machine learning models": 1}, "impacts": ["Designed a robust RESTful API with the MERN stack and employed Material UI and UiPath RPA to create a user-friendly frontend and interface for Astics, streamlining data storage costs by 15%", "Engineered Ruby and MySQL docker container for Hummingbird, which generated transaction data utilizing CycleGANs and ran optimized SQL queries to identify previous fraudulent transactions, catapulting detection accuracy by 20%"], "end_date": "Jul 2023", "location": "San Francisco, CA", "role_title": "Software Developer", "start_date": "Aug 2022", "organization": "Codebase"}, {"skills": {"PCA": 1, "AI models": 1, "Machine Learning": 1}, "impacts": ["Worked under Prof. Bouchard (UCSF/LBNL) to understand biophysical properties of neurons by developing tree and density-based clustering models, trimming interference latency of existing AI models by 65%", "Cut dimensionality variance of features by 45% through statistical methods like PCA, modeling noise from quantitative data"], "end_date": "Aug 2022", "location": "Berkeley, CA", "role_title": "Machine Learning Research Assistant", "start_date": "Jan 2022", "organization": "University of California, Berkeley"}, {"skills": {"AI models": 1, "Machine Learning": 1, "GAN-based machine learning models": 1}, "impacts": ["Devised a novel density-based clustering algorithm for detection of anomalous data points in high-dimensional spaces and big data sets, with ongoing efforts to improve results with GAN-based machine learning models", "Slashed cluster variance by 58% and improved accuracy by 22%, utilizing statistics for data-driven quantitative analytics"], "end_date": "Oct 2022", "location": "Mumbai, India", "role_title": "Machine Learning Research Lead", "start_date": "Sep 2021", "organization": "IEEE"}, {"skills": {"S3": 1, "AWS": 1, "EC2": 1, "MLOps": 1, "OpenCV": 1, "Selenium": 1, "AWS lambda": 1, "TensorFlow": 1, "Kalman filter": 1}, "impacts": ["Implemented real-time user lip coordinate tracking and speech classification with TensorFlow and OpenCV to tackle speech pathology and help individuals with speech impediments, achieving 87% pattern recognition", "Compiled several thousand labeled data points using custom Selenium web scrapers, reducing noise with Kalman filter", "Productionized backend on EC2, with S3 storage buckets and AWS lambda functions, slashing time latencies by around half"], "end_date": "Nov 2021", "location": "Cambridge, MA", "role_title": "Full-Stack Developer", "start_date": "Nov 2021", "organization": "SilverAI"}, {"skills": {"Go": 1, "Flask": 1, "React": 1, "Node.JS": 1, "Postman": 1, "BERT NLP": 1, "Postgres": 1}, "impacts": ["Led team to build a healthcare forum web application on Solana using Go, converting user posts into tradeable NFT tokens", "Incorporated Bootstrap React to create a seamless, personalized frontend and utilized BERT NLP to perform sentiment analysis of comments and posts, boosting concurrent users to several hundreds", "Cut costs by utilizing efficient RESTful Flask and Node.JS APIs on a Heroku server with a Postgres database and conducted rigorous testing using Postman, ensuring robust functionality and stability of data streams"], "end_date": "Aug 2022", "location": "San Francisco, CA", "role_title": "Backend Developer", "start_date": "Aug 2022", "organization": "Faiza"}], "general_skills": {"C": 1, "CD": 1, "CI": 1, "Go": 1, "AWS": 1, "C++": 1, "SQL": 1, "Bash": 1, "Java": 1, "Node": 1, "Ruby": 1, "Flask": 1, "Keras": 1, "Linux": 1, "NumPy": 1, "Docker": 1, "Matlab": 1, "OpenCV": 1, "Pandas": 1, "Python": 1, "VSCode": 1, "Vue.JS": 1, "Postman": 1, "ReactJS": 1, "Seaborn": 1, "HTML & CSS": 1, "JavaScript": 1, "Jupyter Notebooks": 1, "Github Version Controller": 1}, "years_of_experience": 3}] 
fits the category of machine learning engineer. When providing a reasoning, only reference the specific heuristics provided,
all your lines of reasoning should be relevant to the provided heuristic.

Answer: 
reject: 
Based on the information provided, I would reject the candidate, Vardhan Shorewala. The heuristics for a machine learning engineer 
position at ElectroKare include relevant experience in machine learning research and development, good communication skills, a strong 
background in machine learning research, proficiency in relevant technologies, and adaptability. While Vardhan has experience in software 
engineering and algorithm development, his background is not specifically in machine learning research. Additionally, while he has 
demonstrated proficiency in various technologies, there is no evidence of his ability to apply them effectively in machine learning 
solutions. Finally, while he has shown adaptability in his previous roles, there is no indication that he has experience working on complex
technical concepts with non-technical stakeholders. Therefore, based on the provided heuristics, I would reject Vardhan Shorewala as a potential 
candidate for the machine learning engineer position at ElectroKare.

Example 2:
Question: You have a candidate and a label. On the bases of the following heuristcs here: 
Of course, I'd be happy to help! Based on the job description provided, here are 5 precise qualities regarding Education that could make a candidate a strong candidate for the position of machine learning engineer at ElectroKare:
1. Strong background in machine learning research and development: As the job description highlights the importance of critical thinking abilities and research experience in machine learning, a candidate with a strong background in this area would be well-suited for the role. This could include experience with popular machine learning frameworks such as TensorFlow or PyTorch, as well as proficiency in programming languages such as Python or R.
2. Relevant academic degrees: A degree in computer science, engineering, or a related field with a focus on machine learning would be highly desirable for this position. Additionally, candidates with advanced degrees such as Master's or PhDs in these fields may have an advantage due to their deeper understanding of machine learning concepts and techniques.
3. Experience with data analysis and visualization: As ElectroKare is focused on developing innovative electrolyte monitoring technology, a candidate with experience analyzing and visualizing complex data sets would be valuable. This could include experience working with databases, data warehousing tools, or data visualization libraries such as Matplotlib or Seaborn.
4. Familiarity with cloud computing platforms: Given the emphasis on AWS and GCP skills in the job description, candidates who have experience working with cloud computing platforms may have an advantage. This could include experience deploying machine learning models on cloud infrastructure, managing large datasets on cloud storage solutions, or using cloud-based development tools such as Jenkins or Travis CI.
5. Evidence of innovation and creativity: As ElectroKare is looking for engineers who can think outside the box and develop novel solutions to complex problems, candidates who have demonstrated innovation and creativity in their previous work would be highly desirable. This could include patents filed for inventions related to machine learning or electrolyte monitoring technology, publications in top-tier conferences or journals related to these fields, or other forms of recognition for innovative work in these areas. 
Decide whether the following candidate: 
[{"name": "Vardhan Shorewala", "email": "vardhan@berkeley.edu", "links": ["linkedin.com/in/vardhan-shorewala-b85543172/", "github.com/vardhan-shorewala"], "phone": "510-761-1001", "educations": [{"gpa": "3.94", "degree": "Bachelors", "majors": ["Electrical Engineering", "Computer Science", "Business"], "grad_year": "2025", "institution": "University of California, Berkeley"}], "experiences": [{"skills": {"C": 1, "CI": 1, "S3": 1, "AWS": 1, "EC2": 1, "Ruby": 1, "MLOps": 1, "MySQL": 1, "React": 1, "OpenCV": 1, "Fastify": 1, "AkkaHTTP": 1, "Selenium": 1, "Solidity": 1, "AI models": 1, "CD DevOps": 1, "AWS lambda": 1, "MERN stack": 1, "TensorFlow": 1, "UiPath RPA": 1, "Material UI": 1, "Kalman filter": 1, "MetaMask Snap": 1, "AWS Cloud Stack": 1, "Machine Learning": 1, "supply-chain optimization": 1, "GAN-based machine learning models": 1, "Semaphore zero-knowledge cryptography": 1, "bipartite signal processing algorithms": 1}, "impacts": ["Improved match-rate by 35% in supply-chain optimization", "Diminished upstream API calls by 23x, saving upwards of $100,000 monthly", "Validated software architecture with SNS messages, deploying AWS Cloud Stack through CI/CD DevOps for 50K+ vendors"], "end_date": "Aug 2023", "location": "Seattle, WA", "role_title": "Software Engineering Intern", "start_date": "May 2023", "organization": "Amazon"}, {"skills": {"Ruby": 1, "MLOps": 1, "MySQL": 1, "React": 1, "Fastify": 1, "Polygon": 1, "Solidity": 1, "AI models": 1, "MERN stack": 1, "UiPath RPA": 1, "Material UI": 1, "RESTful API": 1, "MetaMask Snap": 1, "Machine Learning": 1, "L1 to L2 transactions": 1, "GAN-based machine learning models": 1, "Semaphore zero-knowledge cryptography": 1}, "impacts": ["Productionized a Voting dApp on Polygon using Solidity and Semaphore zero-knowledge cryptography", "Engineered a React-based dApp and MetaMask Snap for efficient L1 to L2 transactions without bridging contracts for Arbitrium"], "end_date": "Present", "location": "San Francisco, CA", "role_title": "Algorithm Developer", "start_date": "Jan 2023", "organization": "Blockchain at Berkeley"}, {"skills": {"C": 1, "Ruby": 1, "MLOps": 1, "MySQL": 1, "React": 1, "AkkaHTTP": 1, "AI models": 1, "MERN stack": 1, "UiPath RPA": 1, "Material UI": 1, "Machine Learning": 1, "GAN-based machine learning models": 1}, "impacts": ["Designed a robust RESTful API with the MERN stack and employed Material UI and UiPath RPA to create a user-friendly frontend and interface for Astics, streamlining data storage costs by 15%", "Engineered Ruby and MySQL docker container for Hummingbird, which generated transaction data utilizing CycleGANs and ran optimized SQL queries to identify previous fraudulent transactions, catapulting detection accuracy by 20%"], "end_date": "Jul 2023", "location": "San Francisco, CA", "role_title": "Software Developer", "start_date": "Aug 2022", "organization": "Codebase"}, {"skills": {"PCA": 1, "AI models": 1, "Machine Learning": 1}, "impacts": ["Worked under Prof. Bouchard (UCSF/LBNL) to understand biophysical properties of neurons by developing tree and density-based clustering models, trimming interference latency of existing AI models by 65%", "Cut dimensionality variance of features by 45% through statistical methods like PCA, modeling noise from quantitative data"], "end_date": "Aug 2022", "location": "Berkeley, CA", "role_title": "Machine Learning Research Assistant", "start_date": "Jan 2022", "organization": "University of California, Berkeley"}, {"skills": {"AI models": 1, "Machine Learning": 1, "GAN-based machine learning models": 1}, "impacts": ["Devised a novel density-based clustering algorithm for detection of anomalous data points in high-dimensional spaces and big data sets, with ongoing efforts to improve results with GAN-based machine learning models", "Slashed cluster variance by 58% and improved accuracy by 22%, utilizing statistics for data-driven quantitative analytics"], "end_date": "Oct 2022", "location": "Mumbai, India", "role_title": "Machine Learning Research Lead", "start_date": "Sep 2021", "organization": "IEEE"}, {"skills": {"S3": 1, "AWS": 1, "EC2": 1, "MLOps": 1, "OpenCV": 1, "Selenium": 1, "AWS lambda": 1, "TensorFlow": 1, "Kalman filter": 1}, "impacts": ["Implemented real-time user lip coordinate tracking and speech classification with TensorFlow and OpenCV to tackle speech pathology and help individuals with speech impediments, achieving 87% pattern recognition", "Compiled several thousand labeled data points using custom Selenium web scrapers, reducing noise with Kalman filter", "Productionized backend on EC2, with S3 storage buckets and AWS lambda functions, slashing time latencies by around half"], "end_date": "Nov 2021", "location": "Cambridge, MA", "role_title": "Full-Stack Developer", "start_date": "Nov 2021", "organization": "SilverAI"}, {"skills": {"Go": 1, "Flask": 1, "React": 1, "Node.JS": 1, "Postman": 1, "BERT NLP": 1, "Postgres": 1}, "impacts": ["Led team to build a healthcare forum web application on Solana using Go, converting user posts into tradeable NFT tokens", "Incorporated Bootstrap React to create a seamless, personalized frontend and utilized BERT NLP to perform sentiment analysis of comments and posts, boosting concurrent users to several hundreds", "Cut costs by utilizing efficient RESTful Flask and Node.JS APIs on a Heroku server with a Postgres database and conducted rigorous testing using Postman, ensuring robust functionality and stability of data streams"], "end_date": "Aug 2022", "location": "San Francisco, CA", "role_title": "Backend Developer", "start_date": "Aug 2022", "organization": "Faiza"}], "general_skills": {"C": 1, "CD": 1, "CI": 1, "Go": 1, "AWS": 1, "C++": 1, "SQL": 1, "Bash": 1, "Java": 1, "Node": 1, "Ruby": 1, "Flask": 1, "Keras": 1, "Linux": 1, "NumPy": 1, "Docker": 1, "Matlab": 1, "OpenCV": 1, "Pandas": 1, "Python": 1, "VSCode": 1, "Vue.JS": 1, "Postman": 1, "ReactJS": 1, "Seaborn": 1, "HTML & CSS": 1, "JavaScript": 1, "Jupyter Notebooks": 1, "Github Version Controller": 1}, "years_of_experience": 3}] 
fits the category of machine learning engineer. When providing a reasoning, only reference the specific heuristics provided,
all your lines of reasoning should be relevant to the provided heuristic.

Answer:
accept:Based on the provided heuristics, I would accept Vardhan Shorewala as a candidate for the position of machine learning engineer at ElectroKare.
Here are my reasons:
1. Strong background in machine learning research and development: Vardhan has experience working with popular machine learning frameworks such as TensorFlow and PyTorch, as well as proficiency in programming languages such as Python and R. This demonstrates a strong foundation in the field of machine learning, which is essential for success in this role.
2. Relevant academic degrees: Vardhan's degree in Electrical Engineering, Computer Science, and Business with a focus on machine learning aligns perfectly with the job description's emphasis on relevant academic degrees. Additionally, his advanced degrees in these fields may have provided him with a deeper understanding of machine learning concepts and techniques, making him an even more desirable candidate.
3. Experience with data analysis and visualization: As Vardhan has experience working with databases, data warehousing tools, and data visualization libraries such as Seaborn and Matplotlib, he demonstrates proficiency in analyzing and visualizing complex data sets. This skill is crucial for developing innovative electrolyte monitoring technology at ElectroKare.
4. Familiarity with cloud computing platforms: Given the emphasis on AWS skills in the job description, Vardhan's experience deploying machine learning models on cloud infrastructure using AWS lambda functions may be advantageous for this role. His familiarity with cloud computing platforms could enable him to quickly adapt to ElectroKare's technology stack and contribute to the team's efforts to develop novel solutions to complex problems using MLOps practices.
5. Evidence of innovation and creativity: As Vardhan has demonstrated innovation through his patents filed for inventions related to machine learning or electrolyte monitoring technology, publications in top-tier conferences or journals related to these fields, or other forms of recognition for innovative work in these areas; it shows that he has a track record of creativity that could benefit ElectroKare significantly by bringing fresh ideas into their engineering team 

Following the same format above from the examples, what is the answer to this question:
"""


class FewShotPrompter(prompter.Prompter):
    """
    A class for few shot prompting.
    """

    def __init__(self, client: llm.AbstractLLM) -> None:
        self._client = client

    def prompt(self, prompt: str) -> str:
        """
        The abstract method for a prompter to execute a prompt
        """
        final_prompt = f"{NAVIGATION}{prompt}"

        return self._client.query(final_prompt)
