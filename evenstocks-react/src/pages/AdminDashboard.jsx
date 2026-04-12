import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getAllSignedUpUsers } from '../services/api';
import '../styles/AdminDashboard.css';

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  useEffect(() => {
    if (activeSection === 'users') {
      fetchUsers();
    }
  }, [activeSection]);

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const data = await getAllSignedUpUsers();
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    }
    setLoadingUsers(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleNavClick = (section, link) => {
    if (link) {
      navigate(link);
      return;
    }
    setActiveSection(section);
    setSidebarOpen(false);
  };

  const navItems = [
    { id: 'dashboard', icon: 'fa-home', label: 'Dashboard' },
    { id: 'chatbot', icon: 'fa-robot', label: 'AI Chatbot', link: '/chatbot' },
    { id: 'messages', icon: 'fa-envelope', label: 'Messages', badge: '5' },
    { id: 'users', icon: 'fa-user', label: 'Users' },
  ];

  return (
    <div className={`admin-dashboard dashboard-container ${sidebarOpen ? '' : ''}`}>
      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'show' : ''}`}>
        <div className="sidebar-header">
          <img src="https://via.placeholder.com/32x32" alt="Logo" className="logo" />
          <h1>Evenstocks</h1>
        </div>

        <nav className="sidebar-nav">
          <ul>
            {navItems.map((item) => (
              <li key={item.id} className={activeSection === item.id ? 'active' : ''} onClick={() => handleNavClick(item.id, item.link)}>
                <a href="#">
                  <i className={`fas ${item.icon}`}></i>
                  <span>{item.label}</span>
                  {item.badge && <span className="badge">{item.badge}</span>}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile">
            <img src="https://via.placeholder.com/40x40" alt="User Avatar" />
            <div className="user-info">
              <h4>{user?.username || 'Admin User'}</h4>
              <p>admin@example.com</p>
            </div>
            <button className="logout-btn" onClick={handleLogout}>
              <i className="fas fa-sign-out-alt"></i>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="top-header">
          <div className="header-left">
            <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>
              <i className="fas fa-bars"></i>
            </button>
            <h2>{activeSection.charAt(0).toUpperCase() + activeSection.slice(1)}</h2>
          </div>
          <div className="header-right">
            <div className="search-box">
              <i className="fas fa-search"></i>
              <input type="text" placeholder="Search..." />
            </div>
            <div className="notifications">
              <button className="notification-btn">
                <i className="fas fa-bell"></i>
                <span className="badge">3</span>
              </button>
            </div>
            <div className="user-menu">
              <img src="https://via.placeholder.com/32x32" alt="User Avatar" />
              <span>{user?.username || 'Admin'}</span>
              <i className="fas fa-chevron-down"></i>
            </div>
          </div>
        </header>

        <div className="dashboard-content">
          {/* Dashboard Section */}
          {activeSection === 'dashboard' && (
            <section className="content-section active">
              <div className="stats-cards">
                {[
                  { icon: 'fa-wallet', bg: 'bg-primary', value: '$24,300', label: 'Total Revenue', trend: '12%', up: true },
                  { icon: 'fa-users', bg: 'bg-success', value: '1,250', label: 'Total Customers', trend: '8%', up: true },
                  { icon: 'fa-shopping-cart', bg: 'bg-warning', value: '356', label: 'Total Orders', trend: '3%', up: false },
                  { icon: 'fa-chart-pie', bg: 'bg-danger', value: '82%', label: 'Conversion Rate', trend: '5%', up: true },
                ].map((stat, i) => (
                  <div key={i} className="stat-card">
                    <div className={`stat-icon ${stat.bg}`}><i className={`fas ${stat.icon}`}></i></div>
                    <div className="stat-info"><h3>{stat.value}</h3><p>{stat.label}</p></div>
                    <div className="stat-trend">
                      <i className={`fas ${stat.up ? 'fa-arrow-up' : 'fa-arrow-down'}`}></i>
                      <span>{stat.trend}</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="tables-row">
                <div className="table-card">
                  <div className="table-header">
                    <h3>Recent Orders</h3>
                    <button className="btn-view-all">View All</button>
                  </div>
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr><th>Order ID</th><th>Customer</th><th>Date</th><th>Amount</th><th>Status</th><th>Action</th></tr>
                      </thead>
                      <tbody>
                        {[
                          { id: '#ORD-0001', name: 'John Doe', date: '12 May 2023', amount: '$120.00', status: 'completed' },
                          { id: '#ORD-0002', name: 'Jane Smith', date: '11 May 2023', amount: '$85.50', status: 'pending' },
                          { id: '#ORD-0003', name: 'Robert Johnson', date: '10 May 2023', amount: '$220.00', status: 'processing' },
                          { id: '#ORD-0004', name: 'Emily Davis', date: '9 May 2023', amount: '$175.25', status: 'completed' },
                          { id: '#ORD-0005', name: 'Michael Wilson', date: '8 May 2023', amount: '$95.75', status: 'cancelled' },
                        ].map((order, i) => (
                          <tr key={i}>
                            <td>{order.id}</td><td>{order.name}</td><td>{order.date}</td><td>{order.amount}</td>
                            <td><span className={`status-badge ${order.status}`}>{order.status.charAt(0).toUpperCase() + order.status.slice(1)}</span></td>
                            <td><button className="btn-action"><i className="fas fa-ellipsis-v"></i></button></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="activity-card">
                  <div className="activity-header"><h3>Recent Activity</h3></div>
                  <div className="activity-list">
                    {[
                      { icon: 'fa-user', bg: 'bg-primary', text: 'New user registered', time: '5 minutes ago' },
                      { icon: 'fa-shopping-cart', bg: 'bg-success', text: 'New order received', time: '1 hour ago' },
                      { icon: 'fa-exclamation-triangle', bg: 'bg-warning', text: 'High memory usage alert', time: '3 hours ago' },
                      { icon: 'fa-cog', bg: 'bg-info', text: 'System update installed', time: '5 hours ago' },
                      { icon: 'fa-times', bg: 'bg-danger', text: 'Order cancelled', time: '1 day ago' },
                    ].map((activity, i) => (
                      <div key={i} className="activity-item">
                        <div className={`activity-icon ${activity.bg}`}><i className={`fas ${activity.icon}`}></i></div>
                        <div className="activity-content"><p>{activity.text}</p><small>{activity.time}</small></div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Messages Section */}
          {activeSection === 'messages' && (
            <section className="content-section active">
              <div className="table-card">
                <div className="table-header"><h3>Messages</h3></div>
                <div className="table-container">
                  <p style={{ padding: '20px', color: '#666' }}>No messages yet. Messages from the contact form will appear here.</p>
                </div>
              </div>
            </section>
          )}

          {/* Users Section */}
          {activeSection === 'users' && (
            <section className="content-section active">
              <div className="table-card">
                <div className="table-header">
                  <h3>All Signed Up Users</h3>
                  <button className="btn-view-all" onClick={fetchUsers}>Refresh</button>
                </div>
                <div className="table-container">
                  {loadingUsers ? (
                    <div className="loading-spinner"><i className="fas fa-spinner fa-spin"></i><p>Loading users...</p></div>
                  ) : (
                    <table>
                      <thead>
                        <tr><th>#</th><th>Name</th><th>Email</th><th>Username</th><th>Mobile</th><th>Age</th></tr>
                      </thead>
                      <tbody>
                        {users.length > 0 ? users.map((u, i) => (
                          <tr key={i}>
                            <td>{i + 1}</td>
                            <td>{u.fullName || u.full_name || u.name || '-'}</td>
                            <td>{u.email || u.signupEmail || '-'}</td>
                            <td>{u.userName || u.username || '-'}</td>
                            <td>{u.mobile || u.phone || '-'}</td>
                            <td>{u.age || '-'}</td>
                          </tr>
                        )) : (
                          <tr><td colSpan="6" style={{ textAlign: 'center', padding: '20px' }}>No users found.</td></tr>
                        )}
                      </tbody>
                    </table>
                  )}
                </div>
              </div>
            </section>
          )}
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
