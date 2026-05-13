import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.db import load_sql_to_dataframe, execute_query, get_db_connection
from models.reservation import Reservation
from core.auth import hash_password
from utils.helpers import get_current_time
from utils.ui import hide_sidebar
from core.maintenance import process_inactive_users, reorder_user_ids

# =====================================================
# Configuration de la page
# =====================================================
st.set_page_config(
    page_title="OptiStock Admin – Premium Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)
# hide_sidebar()  <-- Supprimé pour laisser apparaître le menu admin

# =====================================================
# Vérification de sécurité
# =====================================================
if 'logged_in' not in st.session_state or not st.session_state.get('logged_in'):
    st.warning("🔒 Accès refusé. Veuillez vous connecter d'abord.")
    st.switch_page("pages/1_Login.py")
    st.stop()

if st.session_state.get('role') != "admin":
    st.error(f"🔒 Accès réservé aux administrateurs. Votre rôle actuel : {st.session_state.get('role')}")
    st.stop()

# =====================================================
# CSS PERSONNALISÉ (Premium Logistics Theme)
# =====================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #f0f4f8;
    }

    /* Glassmorphism Containers */
    .glass-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        margin-bottom: 20px;
    }

    /* KPI Cards */
    .section-title {
        color: #1e293b;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    /* Masquer uniquement la navigation par défaut (liste des fichiers) */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    .kpi-container {
        display: flex;
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .kpi-card {
        flex: 1;
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #005da7;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        transition: transform 0.2s;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
    }

    .kpi-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1e293b;
    }

    .kpi-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .kpi-trend {
        font-size: 0.75rem;
        margin-top: 5px;
    }

    /* Badges */
    .badge {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    .badge-admin { background-color: #fee2e2; color: #dc2626; }
    .badge-owner { background-color: #dbeafe; color: #2563eb; }
    .badge-researcher { background-color: #dcfce7; color: #16a34a; }

    /* Custom Headers */
    .admin-header {
        background: linear-gradient(90deg, #005da7 0%, #003d6e 100%);
        padding: 25px;
        border-radius: 0 0 20px 20px;
        color: white;
        margin-top: -60px;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }

    /* User Detail Styling */
    .detail-section {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("## 🛡️ OptiStock Admin")
    st.image("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
    
    st.divider()
    
    nav_options = {
        "📊 Tableau de Bord": "overview",
        "👥 Utilisateurs": "users",
        "⚙️ Maintenance": "maintenance"
    }
    
    selection = st.radio("Navigation", list(nav_options.keys()))
    admin_view = nav_options[selection]
    
    st.divider()
    if st.button("🚪 Déconnexion", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("pages/1_Login.py")

# =====================================================
# HEADER
# =====================================================
st.markdown(f"""
<div class="admin-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin:0; font-weight:800; font-size:1.8rem;">{selection}</h1>
            <p style="margin:0; opacity:0.8;">Bienvenue, {st.session_state.get('first_name')} — Panel de contrôle sécurisé</p>
        </div>
        <div style="text-align: right;">
            <span class="badge badge-admin">Accès Administrateur</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# =====================================================
# MODULES DE RENDU
# =====================================================

def render_overview():
    # Maintenance auto silencieuse
    process_inactive_users(current_user_id=st.session_state.get("user_id"))
    
    # Récupération des données
    df_u = load_sql_to_dataframe("SELECT role, COUNT(*) as count FROM users GROUP BY role")
    df_w = load_sql_to_dataframe("SELECT status, COUNT(*) as count FROM warehouses GROUP BY status")
    df_r = load_sql_to_dataframe("SELECT status, COUNT(*) as count FROM reservations GROUP BY status")
    
    total_users = df_u['count'].sum() if not df_u.empty else 0
    total_wh = df_w['count'].sum() if not df_u.empty else 0
    total_res = df_r['count'].sum() if not df_u.empty else 0
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Utilisateurs</div>
            <div class="kpi-value">{total_users}</div>
            <div class="kpi-trend" style="color:#16a34a;">↑ 100% actifs</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Entrepôts</div>
            <div class="kpi-value">{total_wh}</div>
            <div class="kpi-trend" style="color:#2563eb;">Gestion Multi-sites</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Réservations</div>
            <div class="kpi-value">{total_res}</div>
            <div class="kpi-trend" style="color:#eab308;">Flux dynamique</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Score Système</div>
            <div class="kpi-value">98%</div>
            <div class="kpi-trend" style="color:#16a34a;">Optimisé</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    
    col_left, col_right = st.columns([6, 4])
    
    with col_left:
        st.markdown("### 📈 Analyse de l'Activité")
        if total_res > 0:
            df_res_hist = load_sql_to_dataframe("SELECT DATE(created_at) as date, COUNT(*) as count FROM reservations GROUP BY DATE(created_at) ORDER BY date")
            fig = px.area(df_res_hist, x='date', y='count', title="Volume de réservations (Historique)",
                          color_discrete_sequence=['#005da7'])
            fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Données insuffisantes pour le graphique d'activité.")
            
        st.markdown("### 📍 Répartition Géographique")
        df_geo = load_sql_to_dataframe("SELECT latitude, longitude, name FROM warehouses")
        if not df_geo.empty:
            st.map(df_geo)

    with col_right:
        st.markdown("### 👥 Profils Utilisateurs")
        if not df_u.empty:
            fig_pie = px.pie(df_u, values='count', names='role', 
                             color='role',
                             color_discrete_map={'admin':'#dc2626', 'owner':'#2563eb', 'researcher':'#16a34a'})
            fig_pie.update_layout(showlegend=False, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown("### 🏢 État du Parc")
        if not df_w.empty:
            fig_bar = px.bar(df_w, x='status', y='count', color='status',
                             color_discrete_map={'available':'#16a34a', 'locked':'#eab308', 'unavailable':'#dc2626'})
            fig_bar.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)

def render_user_details(u_data):
    st.markdown(f"## 🔍 Profil de {u_data['first_name']} {u_data['last_name']}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**Rôle actuel :** {u_data['role'].upper()}")
    with c2:
        st.info(f"**Status :** {'🟢 Actif' if u_data['is_active'] == 1 else '🔴 Suspendu'}")
    with c3:
        st.info(f"**Email :** {u_data['email']}")

    # --- Gestion des Entrepôts ---
    st.markdown("### 🏢 Entrepôts associés")
    df_wh = load_sql_to_dataframe(f"SELECT warehouse_id, name, volume_m3, status, updated_at FROM warehouses WHERE owner_id = {u_data['user_id']}")
    if not df_wh.empty:
        st.dataframe(df_wh, use_container_width=True, hide_index=True)
        st.markdown("#### ⚙️ Maintenance Entrepôts")
        w_to_fix = st.selectbox("Sélectionner un entrepôt :", df_wh['name'].tolist(), key=f"wh_fix_{u_data['user_id']}")
        w_target = df_wh[df_wh['name'] == w_to_fix].iloc[0]
        
        c_wh1, c_wh2 = st.columns(2)
        if c_wh1.button("🟢 Rendre Disponible", use_container_width=True, key=f"btn_avail_{u_data['user_id']}"):
            execute_query("UPDATE warehouses SET status = 'available' WHERE warehouse_id = ?", (w_target['warehouse_id'],))
            st.success(f"'{w_to_fix}' est maintenant disponible."); st.rerun()
        if c_wh2.button("🔴 Rendre Indisponible", use_container_width=True, key=f"btn_unavail_{u_data['user_id']}"):
            execute_query("UPDATE warehouses SET status = 'unavailable' WHERE warehouse_id = ?", (w_target['warehouse_id'],))
            st.warning(f"'{w_to_fix}' est maintenant indisponible."); st.rerun()
    else:
        st.info("Aucun entrepôt trouvé pour cet utilisateur.")

    # --- Suivi des Réservations liées à l'utilisateur ---
    st.markdown("### 📝 Suivi des Réservations")
    query_res = f"""
        SELECT r.reservation_id, w.name as warehouse_name, r.status, r.created_at, r.expires_at 
        FROM reservations r
        JOIN warehouses w ON r.warehouse_id = w.warehouse_id
        WHERE r.researcher_id = {u_data['user_id']} OR w.owner_id = {u_data['user_id']}
        ORDER BY r.created_at DESC
    """
    df_res = load_sql_to_dataframe(query_res)
    if not df_res.empty:
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        st.markdown("#### ⚙️ Action sur Réservation")
        res_id = st.selectbox("ID Réservation :", df_res['reservation_id'].tolist(), key=f"res_sel_{u_data['user_id']}")
        col_res1, col_res2 = st.columns(2)
        if col_res1.button("✅ Confirmer", use_container_width=True, key=f"btn_conf_{u_data['user_id']}"):
            execute_query(f"UPDATE reservations SET status = 'confirmed' WHERE reservation_id = '{res_id}'")
            st.success("Réservation confirmée."); st.rerun()
        if col_res2.button("🚫 Annuler/Libérer", use_container_width=True, key=f"btn_canc_{u_data['user_id']}"):
            execute_query(f"UPDATE reservations SET status = 'canceled' WHERE reservation_id = '{res_id}'")
            st.warning("Réservation annulée."); st.rerun()
    else:
        st.info("Aucune réservation liée à ce profil.")

    # --- Demandes de contact ---
    st.markdown("### 📩 Demandes de Contact")
    df_req = load_sql_to_dataframe(f"SELECT request_id, product_name, message, status, created_at FROM contact_requests WHERE researcher_id = {u_data['user_id']} OR owner_id = {u_data['user_id']}")
    if not df_req.empty:
        st.dataframe(df_req, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune demande de contact détectée.")

    # --- Communications & Interactions ---
    st.markdown("### 💬 Dernières Interactions")
    df_msg = load_sql_to_dataframe(f"SELECT message, created_at FROM chat_messages WHERE sender_id = {u_data['user_id']} ORDER BY created_at DESC LIMIT 5")
    
    df_last = load_sql_to_dataframe(f"""
        SELECT MAX(t.last_date) as last_interaction FROM (
            SELECT created_at as last_date FROM chat_messages WHERE sender_id = {u_data['user_id']}
            UNION
            SELECT created_at as last_date FROM contact_requests WHERE researcher_id = {u_data['user_id']} OR owner_id = {u_data['user_id']}
            UNION
            SELECT updated_at as last_date FROM warehouses WHERE owner_id = {u_data['user_id']}
            UNION
            SELECT updated_at as last_date FROM users WHERE user_id = {u_data['user_id']}
        ) as t
    """)
    
    last_int = df_last.iloc[0]['last_interaction']
    st.success(f"🗓️ **Dernière activité détectée :** {last_int if last_int else 'Inconnue'}")

    if not df_msg.empty:
        st.markdown("#### ✉️ Messages récents")
        for idx, row in df_msg.iterrows():
            st.markdown(f'<div class="detail-section"><small style="color:gray;">{row["created_at"]}</small><br/>{row["message"]}</div>', unsafe_allow_html=True)
    else:
        st.info("Aucun message récent envoyé.")

def render_users_page():
    tab1, tab2, tab3 = st.tabs(["📋 Liste des Comptes", "🔍 Inspecteur de Profil Détallé", "➕ Nouvel Utilisateur"])
    
    with tab1:
        st.markdown("### 👥 Gestion des Comptes")
        
        col_f1, col_f2 = st.columns([3, 1])
        search = col_f1.text_input("🔍 Rechercher par email ou nom...")
        role_filter = col_f2.selectbox("Rôle", ["Tous", "admin", "owner", "researcher"])
        
        query = "SELECT user_id, role, first_name, last_name, email, is_active, created_at FROM users"
        conditions = []
        if search:
            conditions.append(f"(email LIKE '%{search}%' OR first_name LIKE '%{search}%' OR last_name LIKE '%{search}%')")
        if role_filter != "Tous":
            conditions.append(f"role = '{role_filter}'")
            
        if conditions: query += " WHERE " + " AND ".join(conditions)
        df_users = load_sql_to_dataframe(query)
        
        if not df_users.empty:
            df_users['status'] = df_users['is_active'].apply(lambda x: "🟢 Actif" if x == 1 else "🔴 Suspendu")
            st.dataframe(df_users[['user_id', 'role', 'first_name', 'last_name', 'email', 'status', 'created_at']], use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### 🛠️ Actions rapides")
            df_users['label'] = df_users.apply(lambda r: f"{r['email']} ({r['role']})", axis=1)
            target_label = st.selectbox("Sélectionner un compte pour action :", df_users['label'].tolist(), key="quick_action_select")
            u_data = df_users[df_users['label'] == target_label].iloc[0]
            
            c_a, c_b, c_c = st.columns(3)
            with c_a:
                new_status = 0 if u_data['is_active'] == 1 else 1
                label = "Suspendre" if u_data['is_active'] == 1 else "Activer"
                if st.button(f"{label} le compte", use_container_width=True, key=f"btn_status_{u_data['user_id']}"):
                    if u_data['user_id'] == st.session_state.get('user_id'): st.error("Action impossible sur soi.")
                    else: execute_query(f"UPDATE users SET is_active = {new_status} WHERE user_id = {u_data['user_id']}"); st.rerun()
            with c_b:
                if st.button("Réinitialiser ID", use_container_width=True, key=f"btn_reorder_{u_data['user_id']}"):
                    if reorder_user_ids(): st.success("OK"); st.rerun()
            with c_c:
                if st.button("Supprimer", type="primary", use_container_width=True, key=f"btn_del_{u_data['user_id']}"):
                    if u_data['user_id'] == st.session_state.get('user_id'): st.error("Action impossible.")
                    else: execute_query(f"DELETE FROM users WHERE user_id = {u_data['user_id']}"); st.rerun()
        else:
            st.warning("Aucun utilisateur trouvé.")

    with tab2:
        st.markdown("### 🔍 Gestion Centralisée par Utilisateur")
        df_all = load_sql_to_dataframe("SELECT * FROM users")
        if not df_all.empty:
            df_all['display_label'] = df_all.apply(lambda r: f"{r['email']} ({r['role']}) [ID:{r['user_id']}]", axis=1)
            selected_label = st.selectbox("Choisir un utilisateur à inspecter :", df_all['display_label'].tolist(), key="inspect_main_sel")
            inspect_user = df_all[df_all['display_label'] == selected_label].iloc[0]
            render_user_details(inspect_user)
        else:
            st.info("Aucun utilisateur.")

    with tab3:
        with st.container(border=True):
            st.markdown("### ➕ Ajouter un membre")
            with st.form("add_user_premium"):
                col1, col2 = st.columns(2)
                f_name, l_name = col1.text_input("Prénom"), col2.text_input("Nom")
                u_email = st.text_input("Email professionnel")
                u_pwd = st.text_input("Mot de passe temporaire", type="password")
                u_role = st.selectbox("Rôle attribué", ["admin", "owner", "researcher"])
                if st.form_submit_button("🔨 Créer le compte", type="primary"):
                    if f_name and l_name and u_email and u_pwd:
                        from core.auth import create_user
                        ok, msg = create_user(u_role, f_name, l_name, u_email, u_pwd)
                        if ok: st.success("Créé !"); st.rerun()
                        else: st.error(msg)

def render_maintenance():
    st.markdown("### ⚙️ Santé du Système & Maintenance")
    st.write("Cet espace permet d'effectuer des opérations de nettoyage global sur la base de données.")
    
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("#### 🧹 Nettoyage des Comptes Inactifs")
            if st.button("Lancer le nettoyage", type="primary", use_container_width=True):
                count, emails = process_inactive_users(current_user_id=st.session_state.get("user_id"))
                if count > 0:
                    st.success(f"Opération réussie : {count} comptes suspendus.")
                    st.write(f"Utilisateurs concernés : {', '.join(emails)}")
                else:
                    st.info("Aucun compte inactif détecté.")

    with c2:
        with st.container(border=True):
            st.markdown("#### 🔒 Purge Globale des Verrous")
            df_locks = load_sql_to_dataframe("SELECT COUNT(*) as count FROM reservations WHERE status = 'locked'")
            st.metric("Nombre de verrous actifs", df_locks.iloc[0]['count'])
            if st.button("Forcer la libération totale", use_container_width=True):
                execute_query("UPDATE warehouses SET status = 'available' WHERE status = 'locked'")
                execute_query("DELETE FROM reservations WHERE status = 'locked'")
                st.success("Tous les entrepôts ont été débloqués."); st.rerun()

# =====================================================
# MAIN DISPATCHER
# =====================================================
try:
    if admin_view == "overview": render_overview()
    elif admin_view == "users": render_users_page()
    elif admin_view == "maintenance": render_maintenance()
except Exception as e:
    st.error(f"⚠️ Erreur critique : {e}"); st.exception(e)
