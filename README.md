# FACENAME - Dashboard de Inteligência Acadêmica

> **Sistema de Business Intelligence (BI) e Gestão Acadêmica desenvolvido com Django.**

O **FACENAME** é uma solução web projetada para modernizar a gestão educacional. Ele se conecta a um banco de dados legado (MySQL) para transformar dados brutos (notas, faltas e cadastros) em **dashboards analíticos interativos**, permitindo que coordenadores e gestores identifiquem tendências, monitorem o desempenho das turmas e ajam preventivamente em relação a alunos em risco.

---

## ✨ Funcionalidades Principais

### 📊 Dashboards Analíticos (BI)
O sistema vai além da listagem simples, oferecendo uma visão estratégica baseada em dados:

* **KPIs em Tempo Real:** Monitoramento instantâneo do Total de Alunos, Média Geral da Turma e contagem crítica de **Alunos em Risco**.
* **Análise de Desempenho Inteligente:**
    * **Área Destaque:** Identificação automática da área de conhecimento com melhor rendimento (ex: Exatas, Humanas).
    * **Ponto de Atenção:** Alerta automático sobre a disciplina com a menor média da turma.
* **Visualização de Dados (Chart.js):**
    * 📉 **Evolução Bimestral:** Linha do tempo interativa mostrando o progresso da média.
    * 📊 **Distribuição de Notas:** Histograma para entender a dispersão do desempenho (0-4, 4-6, 6-8, 8-10).
    * 🏆 **Ranking de Disciplinas:** Comparativo visual entre as matérias.
* **Gestão de Risco (UX Aprimorada):**
    * Lista de alunos com baixo desempenho acessível via **Modal Interativo**, mantendo o foco na análise macro sem poluir a interface.
    * **Top 3 Alunos:** Ranking visual com fotos para reconhecimento de mérito.

### ⚙️ Ferramentas de Gestão e Importação
* **Importação Inteligente (Excel):**
    * Processamento de planilhas complexas (`.xlsx`, `.xls`).
    * **Lógica de Importação Parcial:** Permite importar notas de um bimestre específico (ex: 1º Bimestre) **sem zerar** ou sobrescrever notas lançadas em bimestres futuros.
    * Criação e atualização automática de Turmas, Alunos e Boletins.
* **Gestão de Identidade:** Upload em massa de fotos dos alunos, associando-as automaticamente pela matrícula.
* **Listagens Avançadas:** Filtros por curso, série, turno e ano, com busca rápida de discentes.

---

## 🛠️ Stack Tecnológico

* **Backend:** Python 3, Django 5.x
* **Frontend:** HTML5, CSS3, Bootstrap 5
* **Charts/BI:** Chart.js
* **Banco de Dados:** MySQL (Integração com legado)
* **Data Science & Processamento:**
    * `pandas` & `openpyxl`: Manipulação de DataFrames e Excel.
    * `Pillow`: Processamento de imagens.
    * `mysqlclient`: Conector de alta performance.

---

## 🚀 Instalação e Execução

Siga os passos abaixo para rodar o projeto localmente:

### 1. Clone o Repositório
```bash
git clone [https://github.com/correia-08/Desgra-aWeb.git](https://github.com/correia-08/Desgra-aWeb.git)
cd Desgra-aWeb

```

### 2. Configure o Ambiente Virtual

Recomendado para isolar as dependências do projeto.

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate

```

**Linux/macOS:**

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt

```

### 4. Configuração do Banco de Dados

Este projeto depende de uma estrutura de banco de dados específica.

1. Certifique-se de ter o **MySQL** instalado e rodando.
2. Crie um banco de dados (schema).
3. **Importante:** Restaure o arquivo SQL fornecido (`dump_facename_...sql`) para criar a estrutura das tabelas e os dados iniciais.
4. Configure as credenciais de acesso no arquivo `projeto/settings.py` (ou utilize um arquivo `.env` se configurado).

### 5. Configuração Inicial (Opcional)

Caso precise popular a estrutura curricular padrão (se não estiver no dump):

```bash
python manage.py default_db

```

### 6. Inicie o Servidor

```bash
python manage.py runserver

```

Acesse o sistema em: `http://127.0.0.1:8000/`

---

## 📖 Como Usar: Importação de Turmas

O coração do sistema é a alimentação de dados via planilhas.

1. Acesse a rota `/importar-turma/`.
2. **Contexto:** Selecione o Curso, Série, Turno e Ano da turma.
3. **Escopo da Importação:**
* Selecione até qual ponto deseja importar (ex: *Recuperação do 1º Semestre*).
* *Nota:* O sistema ignorará colunas da planilha que sejam posteriores ao escopo selecionado, protegendo dados futuros.


4. **Upload:** Anexe o arquivo `.xlsx` da turma.
5. O sistema processará os dados, calculará as médias e atualizará os dashboards automaticamente.

---

## ✒️ Equipe de Desenvolvimento

Este projeto foi desenvolvido como parte de um trabalho acadêmico focado em engenharia de software e análise de dados.

* **Cáthia Kamilly da Silva Andrade**
* **Emanuelle Aparecida Barros Amorim**
* **Filipe Correia da Silva Rocha**
* **Jamily Vieira da Silva**
* **Luís Antônio Barbosa Salviano**
* **Mário Aparecido Leite Almeida**

---

Copyright © 2024-2025 FACENAME Project.
