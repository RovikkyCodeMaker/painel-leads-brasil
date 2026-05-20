import os
import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

app = FastAPI(title="LeadMiner Pro B2B")

DB_NAME = "leads_brasil.db"

def inicializar_banco():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, telefone TEXT, segmento TEXT, cidade TEXT, estado TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM leads")
    if cursor.fetchone()[0] == 0:
        dados = [
            ("Contabilidade Diana", "(11) 97062-0698", "Contabilidade", "São Paulo", "SP"),
            ("SR Contabil", "(11) 3431-3251", "Contabilidade", "São Paulo", "SP"),
            ("Amazonas Fiscais", "(92) 98114-5566", "Contabilidade", "Manaus", "AM"),
            ("Sul Faturamento", "(51) 3224-8899", "Contabilidade", "Porto Alegre", "RS"),
            ("Nordeste Digital", "(81) 3424-7766", "Contabilidade", "Recife", "PE"),
        ]
        for _ in range(5): # Simula volume
            cursor.executemany("INSERT INTO leads (nome, telefone, segmento, cidade, estado) VALUES (?,?,?,?,?)", dados)
        conn.commit()
    conn.close()

inicializar_banco()

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <title>LeadMiner | Dashboard</title>
    <script>
        tailwind.config = {
            theme: {
                extend: {
                    colors: {
                        discordGray: '#313338',
                        discordDeep: '#1e1f22',
                        discordBlurple: '#5865F2',
                        discordGreen: '#23a559'
                    }
                }
            }
        }
    </script>
    <style>
        body { background-color: #313338; color: #dbdee1; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #2b2d31; }
        ::-webkit-scrollbar-thumb { background: #1a1b1e; border-radius: 10px; }
    </style>
</head>
<body class="font-sans antialiased">
    <div class="flex h-screen">
        <div class="w-20 bg-discordDeep flex flex-col items-center py-4 space-y-4 shadow-xl">
            <div class="w-12 h-12 bg-discordBlurple rounded-2xl flex items-center justify-center text-white text-2xl hover:rounded-xl transition-all cursor-pointer">
                <i class="fa-solid fa-bolt"></i>
            </div>
            <div class="w-8 h-1 bg-gray-700 rounded"></div>
            <div class="w-12 h-12 bg-discordGray rounded-3xl flex items-center justify-center text-gray-400 hover:bg-discordBlurple hover:text-white transition-all cursor-pointer">
                <i class="fa-solid fa-database"></i>
            </div>
        </div>

        <div class="flex-1 flex flex-col overflow-hidden">
            <header class="h-16 bg-discordGray border-b border-black/20 flex items-center px-6 justify-between shadow-sm">
                <div class="flex items-center space-x-2">
                    <i class="fa-solid fa-hashtag text-gray-400 text-xl"></i>
                    <h1 class="font-bold text-white uppercase tracking-tight">painel-inteligencia-b2b</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <span class="text-xs bg-discordGreen/20 text-discordGreen px-2 py-1 rounded font-bold italic">SISTEMA ONLINE</span>
                </div>
            </header>

            <main class="flex-1 overflow-y-auto p-6 space-y-6">
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-discordDeep p-4 rounded-lg border border-black/10">
                        <label class="text-xs font-bold text-gray-400">ESTADO DO SCAN</label>
                        <p class="text-2xl text-white font-black">BRASIL <span class="text-discordBlurple">2026</span></p>
                    </div>
                    <div class="bg-discordDeep p-4 rounded-lg border border-black/10">
                        <label class="text-xs font-bold text-gray-400">FILTRAR REGIÃO</label>
                        <select id="select-estado" onchange="carregarDados()" class="w-full mt-1 bg-discordGray border-none rounded p-1 text-white outline-none cursor-pointer">
                            <option value="TODOS text-gray-400"># Selecione o Canal/UF</option>
                            <option value="SP">SP - São Paulo</option>
                            <option value="RS">RS - Rio Grande do Sul</option>
                            <option value="AM">AM - Amazonas</option>
                            <option value="PE">PE - Pernambuco</option>
                        </select>
                    </div>
                    <div class="bg-discordDeep p-4 rounded-lg border border-black/10 flex items-center">
                        <button onclick="baixarExcel()" class="bg-discordBlurple hover:bg-indigo-600 w-full py-3 rounded font-bold text-white transition-colors flex items-center justify-center space-x-2">
                            <i class="fa-solid fa-file-excel"></i>
                            <span>EXPORTAR BASE</span>
                        </button>
                    </div>
                </div>

                <div class="bg-discordDeep rounded-lg border border-black/10 overflow-hidden">
                    <table class="w-full text-left">
                        <thead class="bg-black/20 text-xs text-gray-400 uppercase font-bold">
                            <tr>
                                <th class="px-6 py-3">Empresa</th>
                                <th class="px-6 py-3">Contato</th>
                                <th class="px-6 py-3">Localidade</th>
                                <th class="px-6 py-3 text-center">UF</th>
                            </tr>
                        </thead>
                        <tbody id="tabela-corpo" class="divide-y divide-white/5">
                            </tbody>
                    </table>
                </div>
            </main>
        </div>
    </div>

    <script>
        async function carregarDados() {
            const estado = document.getElementById('select-estado').value;
            const res = await fetch(`/api/leads/${estado}`);
            const dados = await res.json();
            const corpo = document.getElementById('tabela-corpo');
            corpo.innerHTML = dados.map(lead => `
                <tr class="hover:bg-white/[0.02] transition-colors group">
                    <td class="px-6 py-4 font-bold text-discordBlurple underline decoration-transparent group-hover:decoration-discordBlurple cursor-pointer tracking-tight font-medium">${lead.nome}</td>
                    <td class="px-6 py-4 font-mono text-discordGreen text-sm">${lead.telefone}</td>
                    <td class="px-6 py-4 text-gray-400 text-sm">${lead.cidade}</td>
                    <td class="px-6 py-4 text-center"><span class="bg-white/5 text-xs px-2 py-1 rounded text-gray-300 font-bold">${lead.estado}</span></td>
                </tr>
            `).join('');
        }
        function baixarExcel() {
            window.location.href = `/api/exportar/` + document.getElementById('select-estado').value;
        }
        window.onload = carregarDados;
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index(): return HTML_INTERFACE

@app.get("/api/leads/{estado}")
def obter_leads(estado: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    query = "SELECT nome, telefone, segmento, cidade, estado FROM leads"
    params = ()
    if estado.upper() != "TODOS":
        query += " WHERE estado = ?"
        params = (estado.upper(),)
    cursor.execute(query + " LIMIT 100", params)
    linhas = cursor.fetchall()
    conn.close()
    return [dict(l) for l in linhas]

@app.get("/api/exportar/{estado}")
def exportar(estado: str):
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT nome, telefone, segmento, cidade, estado FROM leads"
    if estado.upper() != "TODOS":
        df = pd.read_sql_query(query + " WHERE estado = ?", conn, params=(estado.upper(),))
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    path = "leads_export.xlsx"
    df.to_excel(path, index=False)
    return FileResponse(path, filename=f"leads_{estado.lower()}.xlsx")

if __name__ == "__main__":
    import uvicorn
    import os
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))