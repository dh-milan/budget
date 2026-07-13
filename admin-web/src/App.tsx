import React, { useState } from 'react';
import {
  Users, Activity, DollarSign, Server,
  Menu, Bell, Search, ChevronRight
} from 'lucide-react';

interface StatCard {
  title: string;
  value: string | null;
  change: string | null;
  icon: React.ElementType;
}

const App = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // All stats are null until fetched from the Django Admin API
  const stats: StatCard[] = [
    { title: 'Total Users', value: null, change: null, icon: Users },
    { title: 'Active Subscriptions', value: null, change: null, icon: Activity },
    { title: 'Monthly Revenue', value: null, change: null, icon: DollarSign },
    { title: 'System Health', value: null, change: null, icon: Server },
  ];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside
        className={`bg-gray-900 text-white w-64 flex-shrink-0 transition-all duration-300 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full absolute'
        }`}
      >
        <div className="p-6">
          <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            WealthFlow
          </h1>
          <p className="text-gray-400 text-sm mt-1">Admin Portal</p>
        </div>
        <nav className="mt-6">
          {[
            { label: 'Dashboard', icon: Activity },
            { label: 'User Management', icon: Users },
            { label: 'Revenue Analytics', icon: DollarSign },
            { label: 'System Logs', icon: Server },
          ].map(({ label, icon: Icon }, i) => (
            <a
              key={label}
              href="#"
              className={`flex items-center px-6 py-3 transition-colors ${
                i === 0 ? 'bg-gray-800 border-l-4 border-blue-500' : 'hover:bg-gray-800'
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              <span>{label}</span>
            </a>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full w-full overflow-hidden">
        {/* Header */}
        <header className="bg-white shadow-sm h-16 flex items-center justify-between px-6 z-10 flex-shrink-0">
          <div className="flex items-center">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="text-gray-500 hover:text-gray-700"
            >
              <Menu className="w-6 h-6" />
            </button>
            <div className="ml-6 relative">
              <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search users or transactions..."
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-80 bg-gray-50"
              />
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <button className="text-gray-400 hover:text-gray-600 relative">
              <Bell className="w-6 h-6" />
            </button>
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 to-emerald-500 flex items-center justify-center text-white font-bold text-sm shadow-md">
              A
            </div>
          </div>
        </header>

        {/* Main Dashboard Area */}
        <main className="flex-1 overflow-y-auto p-8">
          <div className="flex justify-between items-end mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Dashboard Overview</h2>
              <p className="text-gray-500 mt-1">Connect the Django Admin API to populate live data.</p>
            </div>
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium shadow-sm transition-colors">
              Generate Report
            </button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, idx) => (
              <div
                key={idx}
                className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-sm font-medium text-gray-500">{stat.title}</p>
                    {stat.value != null ? (
                      <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                    ) : (
                      <div className="h-9 w-28 mt-2 bg-gray-100 rounded animate-pulse" />
                    )}
                  </div>
                  <div
                    className={`p-3 rounded-lg ${
                      idx === 3 ? 'bg-emerald-100 text-emerald-600' : 'bg-blue-50 text-blue-600'
                    }`}
                  >
                    <stat.icon className="w-6 h-6" />
                  </div>
                </div>
                <div className="mt-4">
                  {stat.change != null ? (
                    <span className="text-sm font-medium text-emerald-600">{stat.change}</span>
                  ) : (
                    <div className="h-4 w-24 bg-gray-100 rounded animate-pulse" />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Activity Section Placeholder */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900">Recent System Activity</h3>
              <button className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center">
                View all logs <ChevronRight className="w-4 h-4 ml-1" />
              </button>
            </div>
            <div className="flex flex-col items-center justify-center h-64 bg-gray-50 rounded-lg border border-dashed border-gray-300 gap-3">
              <Activity className="w-12 h-12 text-gray-300" />
              <p className="text-gray-400 font-medium">No activity data yet</p>
              <p className="text-gray-400 text-sm">Wire up <code className="bg-gray-100 px-1 rounded">/api/admin/logs/</code> to populate this view</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
