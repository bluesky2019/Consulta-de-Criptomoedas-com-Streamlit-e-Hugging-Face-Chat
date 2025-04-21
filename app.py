import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from huggingface_hub import InferenceClient

# Configurações iniciais
st.set_page_config(page_title="Cripto Consultor", page_icon="💰", layout="wide")

# Chaves de API (substitua pelas suas)
COINGECKO_API = "https://api.coingecko.com/api/v3"
# Para Hugging Face, você pode usar diretamente ou configurar sua chave
# client = InferenceClient(token="sua_chave_hf")

# Cache para melhor performance
@st.cache_data(ttl=3600)
def get_crypto_list():
    url = f"{COINGECKO_API}/coins/list"
    response = requests.get(url)
    return response.json()

@st.cache_data(ttl=300)
def get_crypto_price(crypto_id, days="max"):
    url = f"{COINGECKO_API}/coins/{crypto_id}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days
    }
    response = requests.get(url, params=params)
    return response.json()

@st.cache_data(ttl=300)
def get_crypto_info(crypto_id):
    url = f"{COINGECKO_API}/coins/{crypto_id}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "false",
        "developer_data": "false",
        "sparkline": "false"
    }
    response = requests.get(url, params=params)
    return response.json()

@st.cache_data(ttl=3600)
def get_news(crypto_id):
    url = f"{COINGECKO_API}/coins/{crypto_id}/news"
    response = requests.get(url)
    return response.json()

def get_chat_response(prompt):
    client = InferenceClient()
    response = client.conversational(prompt)
    return response

def main():
    st.title("💰 Cripto Consultor")
    st.markdown("Consulte informações sobre criptomoedas, visualize gráficos e obtenha as últimas notícias.")
    
    # Obter lista de criptomoedas
    crypto_list = get_crypto_list()
    crypto_names = [crypto["name"] for crypto in crypto_list]
    
    # Selecionar criptomoeda
    selected_crypto = st.selectbox("Selecione uma criptomoeda:", crypto_names)
    
    if selected_crypto:
        crypto_id = next((crypto["id"] for crypto in crypto_list if crypto["name"] == selected_crypto), None)
        
        if crypto_id:
            # Obter informações básicas
            crypto_info = get_crypto_info(crypto_id)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Preço Atual", f"${crypto_info['market_data']['current_price']['usd']:,.2f}")
            with col2:
                st.metric("Variação 24h", f"{crypto_info['market_data']['price_change_percentage_24h']:.2f}%",
                          delta_color="inverse")
            with col3:
                st.metric("Capitalização de Mercado", f"${crypto_info['market_data']['market_cap']['usd']:,.0f}")
            
            # Gráficos
            st.subheader("Gráfico de Preços")
            chart_days = st.radio("Período do gráfico:", ["1D", "7D", "1M", "1Y", "Máximo"], horizontal=True)
            
            days_map = {
                "1D": 1,
                "7D": 7,
                "1M": 30,
                "1Y": 365,
                "Máximo": "max"
            }
            
            price_data = get_crypto_price(crypto_id, days=days_map[chart_days])
            prices = price_data["prices"]
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["date"], y=df["price"], mode="lines", name="Preço"))
            
            fig.update_layout(
                xaxis_title="Data",
                yaxis_title="Preço (USD)",
                hovermode="x unified"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Notícias
            st.subheader("Últimas Notícias")
            if st.button("Atualizar Notícias"):
                st.cache_data.clear()
                
            try:
                news = get_news(crypto_id)
                for item in news[:5]:  # Mostrar apenas as 5 mais recentes
                    with st.expander(item["title"]):
                        st.write(f"**Fonte:** {item.get('source', {}).get('name', 'Desconhecido')}")
                        st.write(f"**Data:** {item.get('date', 'Desconhecida')}")
                        st.write(item.get("description", "Sem descrição disponível."))
                        st.markdown(f"[Leia mais]({item['url']})")
            except:
                st.warning("Não foi possível carregar as notícias no momento.")
            
            # Chat com Hugging Face
            st.subheader("Consultar sobre a Criptomoeda")
            user_input = st.text_input(f"Faça uma pergunta sobre {selected_crypto}:")
            
            if user_input:
                prompt = f"Responda como um especialista em criptomoedas. O usuário está perguntando sobre {selected_crypto}. Pergunta: {user_input}"
                with st.spinner("Processando sua pergunta..."):
                    try:
                        response = get_chat_response(prompt)
                        st.write(response)
                    except Exception as e:
                        st.error(f"Erro ao acessar o serviço de chat: {e}")
        else:
            st.error("ID da criptomoeda não encontrado.")

if __name__ == "__main__":
    main()