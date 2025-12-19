import React, { useState, useEffect, Component } from 'react';
import { 
  ShieldCheck, Wallet, Users, LogOut, Menu, Plus, History,
  FileText, X, Search, ChevronRight, ArrowLeft,
  CheckCircle2, CreditCard, Eye, Download, CloudLightning, Accessibility,
  AlertTriangle, Share2, Flame, Lock, ClipboardPaste, Trash2, Edit2, Save
} from 'lucide-react';

// --- FIREBASE IMPORTS ---
import { initializeApp } from "firebase/app";
import { 
  getFirestore, collection, addDoc, onSnapshot, 
  query, orderBy, serverTimestamp, deleteDoc, doc, updateDoc 
} from 'firebase/firestore';
import { 
  getAuth, signInWithEmailAndPassword, createUserWithEmailAndPassword, 
  signOut, onAuthStateChanged 
} from 'firebase/auth';
import * as XLSX from 'xlsx'; // Ensure this is available via CDN in index.html

// --- 1. CONFIGURATION ---
const firebaseConfig = {
  apiKey: "AIzaSyBOlHLgbNP-l5pouDKrJoEM-6D8IlGgfYY",
  authDomain: "digital-treasurer.firebaseapp.com",
  projectId: "digital-treasurer",
  storageBucket: "digital-treasurer.firebasestorage.app",
  messagingSenderId: "373137625124",
  appId: "1:373137625124:web:208a214488f19fa83748b1",
  measurementId: "G-KBF15P2F06"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);           
const db = getFirestore(app);        

// --- 2. ERROR BOUNDARY ---
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error) { return { hasError: true }; }
  render() {
    if (this.state.hasError) return <div className="h-screen bg-black text-white flex items-center justify-center p-4 text-center"><h1>Something went wrong. Please reload.</h1></div>;
    return this.props.children;
  }
}

// --- 3. UTILITIES ---
const parseCSV = (str) => {
  const arr = [];
  let quote = false;
  for (let row = 0, col = 0, c = 0; c < str.length; c++) {
    let cc = str[c], nc = str[c+1];
    arr[row] = arr[row] || [];
    arr[row][col] = arr[row][col] || '';
    if (cc == '"' && quote && nc == '"') { arr[row][col] += cc; ++c; continue; }
    if (cc == '"') { quote = !quote; continue; }
    if (cc == ',' && !quote) { ++col; continue; }
    if (cc == '\r' && nc == '\n' && !quote) { ++row; col = 0; ++c; continue; }
    if (cc == '\n' && !quote) { ++row; col = 0; continue; }
    if (cc == '\r' && !quote) { ++row; col = 0; continue; }
    arr[row][col] += cc;
  }
  return arr;
};

const parseMpesaSMS = (text) => {
  const codeMatch = text.match(/^([A-Z0-9]{10})\s/);
  const amountMatch = text.match(/Ksh([\d,]+\.\d{2})/);
  const nameMatch = text.match(/from\s(.*?)\s\d{10}/); 

  let code = codeMatch ? codeMatch[1] : "";
  let amount = amountMatch ? amountMatch[1].replace(/,/g, '') : "";
  let fName = "", sName = "";

  if (nameMatch && nameMatch[1]) {
    const fullName = nameMatch[1].trim().split(" ");
    fName = fullName[0] || "";
    sName = fullName.slice(1).join(" ") || "";
  }

  return { code, amount, fName, sName };
};

// --- 4. DATA HOOKS ---
const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const unsub = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
    });
    return () => unsub();
  }, []);

  const login = (email, pass) => signInWithEmailAndPassword(auth, email, pass);
  const register = (email, pass) => createUserWithEmailAndPassword(auth, email, pass);
  const logout = () => signOut(auth);

  return { user, loading, login, register, logout };
};

const useGroups = (user) => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    if (!user) { setGroups([]); setLoading(false); return; }
    const q = query(collection(db, 'groups'), orderBy('name'));
    const unsub = onSnapshot(q, (snap) => {
      setGroups(snap.docs.map(doc => ({ id: doc.id, ...doc.data() })));
      setLoading(false);
    }, (e) => { console.error(e); setLoading(false); });
    return () => unsub();
  }, [user]);

  const addGroup = async (name, eventType, hasFirewood) => {
    if(!name) return;
    await addDoc(collection(db, 'groups'), { 
      name, 
      eventType,
      hasFirewood, 
      created_at: serverTimestamp(), 
      created_by: user.uid 
    });
  };

  const deleteGroup = async (id) => {
    if(!id) return;
    if(window.confirm("Are you sure you want to delete this group? This cannot be undone.")) {
      try {
        await deleteDoc(doc(db, 'groups', id));
      } catch (e) {
        alert("Error deleting group: " + e.message);
      }
    }
  };

  const updateGroup = async (id, updates) => {
    if(!id) return;
    try {
      await updateDoc(doc(db, 'groups', id), updates);
    } catch (e) {
      alert("Error updating group: " + e.message);
    }
  };

  return { groups, loading, addGroup, deleteGroup, updateGroup };
};

const useContributions = (groupName) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    if (!groupName) return;
    setLoading(true);
    const q = query(collection(db, 'contributions'), orderBy('date_added', 'desc'));
    const unsub = onSnapshot(q, (snap) => {
        const filtered = snap.docs
          .map(doc => ({ id: doc.id, ...doc.data() }))
          .filter(d => d.group_name === groupName);
        setData(filtered);
        setLoading(false);
    });
    return () => unsub();
  }, [groupName]);

  const addContribution = async (entry) => {
    return await addDoc(collection(db, 'contributions'), { ...entry, date_added: new Date().toISOString() });
  };
  return { data, loading, addContribution };
};

// --- 5. UI COMPONENTS ---
const Button = ({ children, onClick, variant='primary', className='', icon: Icon, highContrast, disabled }) => {
  const base = "rounded-xl font-bold transition-all active:scale-95 flex items-center justify-center gap-2 py-3 px-6 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed";
  const styles = highContrast 
    ? { primary: "bg-yellow-400 text-black border-2 border-white", accent: "bg-white text-black border-2 border-white", danger: "bg-red-600 text-white border-2 border-white" }
    : { primary: "bg-blue-600 text-white hover:bg-blue-500", accent: "bg-emerald-600 text-white hover:bg-emerald-500", danger: "bg-red-500/20 text-red-200 border border-red-500/50 hover:bg-red-500/30" };
  
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${styles[variant] || styles.primary} ${className}`}>
      {Icon && <Icon size={20} />} {children}
    </button>
  );
};

const Input = ({ label, value, onChange, placeholder, type="text", highContrast }) => (
  <div className="mb-4">
    <label className={`block font-bold text-xs uppercase mb-1 ${highContrast ? 'text-yellow-400' : 'text-blue-200'}`}>{label}</label>
    <input 
      type={type}
      className={`w-full rounded-lg p-3 outline-none ${highContrast ? 'bg-white text-black font-bold border-2 border-white' : 'bg-white/10 text-white border border-white/20 focus:border-blue-500'}`}
      value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
    />
  </div>
);

const GlassCard = ({ children, className='', highContrast }) => (
  <div className={`overflow-hidden rounded-2xl ${highContrast ? 'bg-black border-4 border-white' : 'bg-[#1e293b]/80 backdrop-blur-xl border border-white/10 shadow-2xl'} ${className}`}>
    {children}
  </div>
);

// --- 6. MAIN APP ---
export default function DigitalTreasurer() {
  const { user, loading, login, register, logout } = useAuth();
  const [highContrast, setHighContrast] = useState(false);
  const [urlGroup, setUrlGroup] = useState(null);
  const [isPublicMode, setIsPublicMode] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const g = params.get('group');
    const p = params.get('public');
    if (g) {
      setUrlGroup(decodeURIComponent(g));
      if (p === 'true') setIsPublicMode(true);
    }
  }, []);

  if (loading) return <div className="h-screen bg-slate-900 flex items-center justify-center text-white">Loading system...</div>;

  return (
    <ErrorBoundary>
      <div className={`min-h-screen ${highContrast ? 'bg-black text-white' : 'bg-[#0b1121] text-white'} font-sans`}>
        <div className="fixed top-4 right-4 z-50 flex gap-2">
          <button onClick={() => setHighContrast(!highContrast)} className={`p-2 rounded-full ${highContrast ? 'bg-yellow-400 text-black' : 'bg-white/10'}`}>
            {highContrast ? <Eye size={24}/> : <Accessibility size={24}/>}
          </button>
        </div>
        {isPublicMode ? <PublicDashboard groupName={urlGroup} highContrast={highContrast} /> : (user ? <AdminApp user={user} logout={logout} highContrast={highContrast} /> : <AuthScreen login={login} register={register} highContrast={highContrast} />)}
      </div>
    </ErrorBoundary>
  );
}

// --- 7. AUTH SCREEN ---
function AuthScreen({ login, register, highContrast }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAuth = async () => {
    if(!email || !pass) { setError("Please fill all fields"); return; }
    setLoading(true); setError('');
    try {
      if(isRegister) await register(email, pass);
      else await login(email, pass);
    } catch (e) { setError(e.message.replace("Firebase: ", "")); }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-600 rounded-3xl mb-4 shadow-xl"><Lock size={40} className="text-white" /></div>
          <h1 className="text-3xl font-bold mb-2">Digital Treasurer</h1>
          <p className="opacity-70">Admin Access Portal</p>
        </div>
        <GlassCard className="p-8" highContrast={highContrast}>
          <h2 className="text-xl font-bold mb-6 text-center">{isRegister ? "Create Account" : "Welcome Back"}</h2>
          <Input label="Email Address" value={email} onChange={setEmail} placeholder="admin@treasurer.com" highContrast={highContrast} />
          <Input label="Password" type="password" value={pass} onChange={setPass} placeholder="••••••" highContrast={highContrast} />
          {error && <div className="p-3 bg-red-500/20 text-red-200 text-sm rounded-lg mb-4">{error}</div>}
          <Button onClick={handleAuth} className="w-full mb-4" disabled={loading}>{loading ? "Processing..." : (isRegister ? "Register" : "Login")}</Button>
          <p className="text-center text-sm opacity-60 cursor-pointer hover:text-white" onClick={() => setIsRegister(!isRegister)}>{isRegister ? "Already have an account? Login" : "New Admin? Create Account"}</p>
        </GlassCard>
      </div>
    </div>
  );
}

// --- 8. ADMIN APP ---
function AdminApp({ user, logout, highContrast }) {
  const [activeGroupData, setActiveGroupData] = useState(null);
  const { groups, addGroup, deleteGroup, updateGroup } = useGroups(user);

  return activeGroupData ? (
    <Workspace 
      user={user} 
      groupData={activeGroupData} 
      onExit={() => setActiveGroupData(null)} 
      highContrast={highContrast} 
    />
  ) : (
    <GroupPicker 
      user={user} 
      groups={groups}
      addGroup={addGroup}
      deleteGroup={deleteGroup}
      updateGroup={updateGroup}
      onSelect={setActiveGroupData} 
      logout={logout}
      highContrast={highContrast} 
    />
  );
}

// --- 9. GROUP PICKER ---
function GroupPicker({ user, groups, addGroup, deleteGroup, updateGroup, onSelect, logout, highContrast }) {
  const [formMode, setFormMode] = useState('closed'); // closed, create, edit
  const [formData, setFormData] = useState({ id: null, name: '', eventType: 'Burial', hasFirewood: false });

  const openCreate = () => {
    setFormData({ id: null, name: '', eventType: 'Burial', hasFirewood: false });
    setFormMode('create');
  };

  const openEdit = (group) => {
    setFormData({ id: group.id, name: group.name, eventType: group.eventType, hasFirewood: group.hasFirewood });
    setFormMode('edit');
  };

  const handleSubmit = async () => {
    if (!formData.name) return;
    
    if (formMode === 'create') {
      await addGroup(formData.name, formData.eventType, formData.hasFirewood);
    } else if (formMode === 'edit') {
      await updateGroup(formData.id, {
        name: formData.name,
        eventType: formData.eventType,
        hasFirewood: formData.hasFirewood
      });
    }
    setFormMode('closed');
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-md">
        <div className="flex justify-between items-center mb-8"><h1 className="text-2xl font-bold">Your Groups</h1><button onClick={logout} className="text-red-400 text-sm font-bold flex gap-1 items-center"><LogOut size={14}/> Logout</button></div>
        <GlassCard highContrast={highContrast} className="p-6 min-h-[400px]">
          {formMode === 'closed' ? (
            <>
              <Button onClick={openCreate} className="w-full mb-6" highContrast={highContrast} icon={Plus}>Create New Group</Button>
              <div className="space-y-2">
                {groups.map(g => (
                  <div key={g.id} className={`w-full p-4 rounded-xl flex justify-between items-center ${highContrast ? 'bg-white text-black border-2' : 'bg-white/5 hover:bg-white/10'}`}>
                    <div onClick={() => onSelect(g)} className="cursor-pointer flex-1">
                      <div className="font-bold">{g.name}</div>
                      <div className="text-xs opacity-70">{g.eventType} • {g.hasFirewood ? 'Money + Firewood' : 'Money Only'}</div>
                    </div>
                    
                    <div className="flex gap-2 ml-2">
                      <button onClick={(e) => { e.stopPropagation(); openEdit(g); }} className="p-2 text-blue-300 hover:text-white bg-white/5 rounded-lg"><Edit2 size={16}/></button>
                      <button onClick={(e) => { e.stopPropagation(); deleteGroup(g.id); }} className="p-2 text-red-400 hover:text-red-200 bg-red-500/10 rounded-lg"><Trash2 size={16}/></button>
                    </div>
                  </div>
                ))}
                {groups.length === 0 && <div className="text-center opacity-50 py-8">No groups found.</div>}
              </div>
            </>
          ) : (
            <div className="animate-fadeIn">
              <h3 className="text-xl font-bold mb-4">{formMode === 'create' ? "New Group Details" : "Edit Group Details"}</h3>
              <Input label="Group Name" value={formData.name} onChange={(v) => setFormData({...formData, name: v})} placeholder="e.g. Grandma's Visit" highContrast={highContrast} />
              
              <div className="mb-4">
                <label className="block font-bold text-xs uppercase mb-1 text-blue-200">Event Type</label>
                <select 
                  value={formData.eventType} 
                  onChange={e => setFormData({...formData, eventType: e.target.value})}
                  className="w-full bg-slate-800 p-3 rounded-lg text-white border border-white/20"
                >
                  <option value="Burial">Burial</option>
                  <option value="Wedding">Wedding</option>
                  <option value="Visiting Parents">Visiting Parents</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="mb-6">
                 <label className="block font-bold text-xs uppercase mb-2 text-blue-200">Contribution Type</label>
                 <div className="flex gap-2">
                    <button onClick={() => setFormData({...formData, hasFirewood: false})} className={`flex-1 py-3 rounded-lg text-xs font-bold border transition-all ${!formData.hasFirewood ? 'bg-blue-600 border-blue-600 text-white' : 'border-white/20 text-white/50'}`}>Money Only</button>
                    <button onClick={() => setFormData({...formData, hasFirewood: true})} className={`flex-1 py-3 rounded-lg text-xs font-bold border transition-all ${formData.hasFirewood ? 'bg-orange-600 border-orange-600 text-white' : 'border-white/20 text-white/50'}`}>Money + Firewood</button>
                 </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={handleSubmit} className="flex-1" icon={Save}>{formMode === 'create' ? "Create" : "Update"}</Button>
                <Button onClick={() => setFormMode('closed')} variant="accent" className="flex-1">Cancel</Button>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  );
}

// --- 10. WORKSPACE ---
function Workspace({ user, groupData, onExit, highContrast }) {
  const { data, addContribution } = useContributions(groupData.name);
  const [view, setView] = useState('home');
  const copyPublicLink = () => {
    const url = `${window.location.origin}/?group=${encodeURIComponent(groupData.name)}&public=true`;
    navigator.clipboard.writeText(url);
    alert("Public Link Copied!");
  };
  const renderView = () => {
    switch(view) {
      case 'add': return <AddForm groupData={groupData} onSave={addContribution} onBack={() => setView('home')} highContrast={highContrast} />;
      case 'import': return <ImportForm groupData={groupData} onSave={addContribution} onBack={() => setView('home')} highContrast={highContrast} />;
      case 'report': return <ReportView groupData={groupData} data={data} onBack={() => setView('home')} highContrast={highContrast} />;
      case 'history': return <HistoryView groupData={groupData} data={data} onBack={() => setView('home')} highContrast={highContrast} />;
      default: return (
        <div className="max-w-3xl mx-auto pb-20">
          <div className="flex justify-between items-center mb-6"><button onClick={onExit} className="flex items-center gap-2 text-blue-300"><ArrowLeft size={20}/> Exit</button><button onClick={copyPublicLink} className="flex items-center gap-2 text-emerald-400 border border-emerald-400 px-3 py-1 rounded-full text-sm hover:bg-emerald-400/10"><Share2 size={14} /> Share Public Link</button></div>
          <GlassCard className="p-6 mb-6 bg-gradient-to-r from-blue-900/50 to-purple-900/50" highContrast={highContrast}><h2 className="text-3xl font-bold mb-1">{groupData.name}</h2><div className="text-sm opacity-70 mb-4">{groupData.eventType}</div><div className="text-4xl font-bold text-emerald-400">KES {data.reduce((a,b) => a + (Number(b.amount)||0), 0).toLocaleString()}</div><div className="text-xs uppercase tracking-widest mt-1 opacity-60">Total Collected</div></GlassCard>
          <div className="grid grid-cols-2 gap-3 mb-8"><Button onClick={() => setView('add')} icon={Plus}>Add Entry</Button><Button onClick={() => setView('import')} icon={CloudLightning} variant="accent">Import CSV</Button><Button onClick={() => setView('report')} icon={FileText}>Report</Button><Button onClick={() => setView('history')} icon={History} className="bg-orange-600 hover:bg-orange-500">History/Excel</Button></div>
          <h3 className="font-bold text-lg mb-4">Recent Transactions</h3>
          <div className="space-y-2">{data.slice(0, 5).map(d => (<div key={d.id} className="p-4 rounded-xl bg-white/5 flex justify-between items-center"><div><div className="font-bold">{d.first_name} {d.second_name}</div><div className="text-xs opacity-60 flex gap-2"><span>{d.mpesa_code}</span>{d.firewood && <span className="text-orange-400 flex items-center gap-1"><Flame size={10}/> Firewood</span>}</div></div><div className="font-bold text-emerald-400">+{Number(d.amount).toLocaleString()}</div></div>))}</div>
        </div>
      );
    }
  };
  return <div className="p-4 min-h-screen animate-fadeIn">{renderView()}</div>;
}

// --- 11. PUBLIC DASHBOARD ---
function PublicDashboard({ groupName, highContrast }) {
  const { data, loading } = useContributions(groupName);
  const total = data.reduce((a,b) => a + (Number(b.amount)||0), 0);
  return (
    <div className="p-4 max-w-3xl mx-auto min-h-screen">
      <div className="text-center mb-8 mt-4"><div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4 shadow-lg"><ShieldCheck size={32} /></div><h1 className="text-2xl font-bold">{groupName}</h1><p className="text-emerald-400 text-sm font-bold uppercase tracking-widest">Transparency Portal</p></div>
      <GlassCard className="p-8 text-center mb-8" highContrast={highContrast}><div className="text-sm opacity-60 mb-2">TOTAL CONTRIBUTIONS</div><div className="text-5xl font-bold text-white">KES {total.toLocaleString()}</div></GlassCard>
      <div className="flex justify-between items-end mb-4 px-2"><h3 className="font-bold text-lg">Full List</h3><div className="text-xs opacity-50">{data.length} Records</div></div>
      <div className="space-y-2 pb-20">{loading && <div className="text-center opacity-50">Loading live data...</div>}{data.map(d => (<div key={d.id} className={`p-4 rounded-xl flex justify-between items-center ${highContrast ? 'bg-white text-black border-2' : 'bg-white/5 border border-white/5'}`}><div className="flex items-center gap-3"><div className="w-10 h-10 rounded-full bg-blue-500/20 text-blue-300 flex items-center justify-center font-bold">{d.first_name?.[0]}</div><div><div className="font-bold">{d.first_name} {d.second_name}</div><div className="text-xs opacity-60 flex gap-2"><span>{d.mpesa_code}</span>{d.firewood && <span className="text-orange-400 flex items-center gap-1"><Flame size={10}/> Firewood</span>}</div></div></div><div className="font-mono font-bold">KES {Number(d.amount).toLocaleString()}</div></div>))}<div className="text-center text-xs opacity-30 mt-8 pt-8 border-t border-white/10">System Developed By: LilianMawia2025</div></div>
    </div>
  );
}

// --- 12. FORMS ---
function AddForm({ groupData, onSave, onBack, highContrast }) {
  const [fName, setFName] = useState('');
  const [sName, setSName] = useState('');
  const [amount, setAmount] = useState('');
  const [code, setCode] = useState('');
  const [firewood, setFirewood] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pasteMode, setPasteMode] = useState(false);
  const [pasteText, setPasteText] = useState('');

  const handlePasteProcess = () => {
    const { code: c, amount: a, fName: f, sName: s } = parseMpesaSMS(pasteText);
    if(c || a) {
      setCode(c);
      setAmount(a);
      if(f) setFName(f);
      if(s) setSName(s);
      setPasteMode(false);
    } else {
      alert("Could not detect M-Pesa details. Please enter manually.");
    }
  };

  const handleSubmit = async () => {
    if(!fName) return;
    setSaving(true);
    await onSave({ group_name: groupData.name, first_name: fName, second_name: sName, amount: parseFloat(amount) || 0, mpesa_code: code || 'CASH', firewood });
    setSaving(false);
    onBack();
  };

  return (
    <div className="max-w-xl mx-auto">
      <button onClick={onBack} className="mb-4 text-blue-300 flex gap-2"><ArrowLeft/> Back</button>
      <GlassCard className="p-6" highContrast={highContrast}>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Add Contribution</h2>
          <button onClick={() => setPasteMode(!pasteMode)} className="text-xs bg-emerald-600/20 text-emerald-400 px-3 py-1 rounded-full flex gap-1 items-center border border-emerald-500/30">
            <ClipboardPaste size={12}/> Auto-Fill from SMS
          </button>
        </div>

        {pasteMode && (
          <div className="mb-6 p-4 bg-emerald-900/20 border border-emerald-500/30 rounded-xl animate-fadeIn">
            <p className="text-xs text-emerald-200 mb-2">Paste M-Pesa message here:</p>
            <textarea className="w-full bg-black/40 p-2 rounded text-xs text-white h-20 mb-2" value={pasteText} onChange={e => setPasteText(e.target.value)} placeholder="QWE123TY Confirmed..."></textarea>
            <Button onClick={handlePasteProcess} size="small" className="w-full py-2">Extract Details</Button>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <Input label="First Name" value={fName} onChange={setFName} highContrast={highContrast} />
          <Input label="Second Name" value={sName} onChange={setSName} highContrast={highContrast} />
        </div>
        <Input label="Amount (KES)" value={amount} onChange={setAmount} highContrast={highContrast} />
        <Input label="M-Pesa Code" value={code} onChange={setCode} placeholder="e.g. QWE123TY" highContrast={highContrast} />
        
        {groupData.hasFirewood && (
          <div className="flex items-center gap-3 mb-8 p-4 bg-white/5 rounded-lg border border-white/10 cursor-pointer" onClick={() => setFirewood(!firewood)}>
            <div className={`w-6 h-6 rounded border flex items-center justify-center ${firewood ? 'bg-orange-500 border-orange-500' : 'border-white/30'}`}>{firewood && <CheckCircle2 size={16} />}</div>
            <span className="font-bold text-sm">Firewood Received?</span>
          </div>
        )}
        <Button onClick={handleSubmit} className="w-full" disabled={saving}>{saving ? 'Saving...' : 'Save Record'}</Button>
      </GlassCard>
    </div>
  );
}

function ImportForm({ groupData, onSave, onBack, highContrast }) {
  const [csvText, setCsvText] = useState('');
  const [status, setStatus] = useState('');
  const [processing, setProcessing] = useState(false);

  const processCSV = async () => {
    const rows = parseCSV(csvText);
    let count = 0;
    const promises = [];
    rows.forEach((row, i) => {
        if (i < 1 || row.length < 3) return; 
        let code = row[0]; let details = row[2] || row[0]; let amount = row[4] || row[1];
        let cleanAmt = typeof amount === 'string' ? parseFloat(amount.replace(/,/g, '')) : amount;
        if (cleanAmt && !isNaN(cleanAmt)) {
            const nameParts = details.split(" ");
            promises.push(onSave({ group_name: groupData.name, first_name: nameParts[0] || "Unknown", second_name: nameParts[1] || "", amount: cleanAmt, mpesa_code: code, firewood: false }));
            count++;
        }
    });
    if (count > 0) { setProcessing(true); await Promise.all(promises); setStatus(`Imported ${count} records successfully!`); setTimeout(onBack, 1500); } else { setStatus("No valid records found."); }
  };
  return (
    <div className="max-w-xl mx-auto"><button onClick={onBack} className="mb-4 text-blue-300 flex gap-2"><ArrowLeft/> Back</button>
      <GlassCard className="p-6" highContrast={highContrast}><h2 className="text-xl font-bold mb-2">Import M-Pesa CSV</h2><p className="text-xs opacity-60 mb-4">Paste the content of your CSV file below.</p><textarea className="w-full h-40 bg-black/30 p-4 rounded-xl text-xs font-mono border border-white/20 mb-4 text-white" placeholder="Paste CSV data here..." value={csvText} onChange={e => setCsvText(e.target.value)} />{status && <div className="text-emerald-400 font-bold mb-4 text-center">{status}</div>}<Button onClick={processCSV} className="w-full" disabled={processing}>{processing ? 'Uploading...' : 'Process Data'}</Button></GlassCard>
    </div>
  );
}

function ReportView({ groupData, data, onBack, highContrast }) {
  const generate = () => {
    const total = data.reduce((a,b) => a + (Number(b.amount)||0), 0);
    const date = new Date().toLocaleDateString();
    let txt = `*${groupData.name.toUpperCase()}*\n`; txt += `Events: ${groupData.eventType}\n`; txt += `📅 ${date}\n\n`; txt += `*CONTRIBUTIONS LIST:*\n`;
    data.forEach((d, i) => { const fw = d.firewood ? " (+🪵 Firewood)" : ""; txt += `${i+1}. ${d.first_name} ${d.second_name} (${d.mpesa_code}): KES ${d.amount}${fw}\n`; });
    txt += `\n💰 *TOTAL: KES ${total.toLocaleString()}*\n`; txt += `\n💎 *System by LilianMawia2025*`; return txt;
  };
  const copy = () => { navigator.clipboard.writeText(generate()); alert("Report copied to clipboard!"); };
  return (
    <div className="max-w-xl mx-auto"><button onClick={onBack} className="mb-4 text-blue-300 flex gap-2"><ArrowLeft/> Back</button>
      <GlassCard className="p-6" highContrast={highContrast}><div className="bg-black/30 p-4 rounded-xl font-mono text-xs whitespace-pre-wrap mb-4 h-64 overflow-y-auto text-white">{generate()}</div><div className="grid grid-cols-2 gap-2"><Button onClick={copy}>Copy Text</Button><Button onClick={onBack} variant="accent">Close</Button></div></GlassCard>
    </div>
  );
}

function HistoryView({ groupData, data, onBack, highContrast }) {
    const handleDownloadExcel = () => {
        const XLSX = window.XLSX;
        if (!XLSX) { alert("Excel library is still loading..."); return; }
        const formattedData = data.map(item => ({ Date: new Date(item.date_added).toLocaleDateString(), "First Name": item.first_name, "Second Name": item.second_name, "M-Pesa Code": item.mpesa_code, Amount: item.amount, "Firewood": item.firewood ? "Yes" : "No" }));
        formattedData.push({}); formattedData.push({ Date: '', "First Name": 'System Developed By:', "Second Name": 'LilianMawia2025', "M-Pesa Code": '', Amount: '', "Firewood": '' });
        const worksheet = XLSX.utils.json_to_sheet(formattedData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Contributions");
        XLSX.writeFile(workbook, `${groupData.name}_Data.xlsx`);
    };
    return (
        <div className="max-w-4xl mx-auto h-full flex flex-col"><div className="flex items-center justify-between mb-6"><button onClick={onBack} className="flex items-center gap-2 text-blue-300"><ArrowLeft size={20}/> Back</button><Button onClick={handleDownloadExcel} variant="accent" icon={Download} highContrast={highContrast}>Download Excel</Button></div>
             <GlassCard className="flex-1 overflow-hidden flex flex-col p-0 md:p-0" highContrast={highContrast}><div className="overflow-y-auto flex-1"><table className="w-full text-left"><thead className={`sticky top-0 z-10 ${highContrast ? 'bg-white text-black font-black' : 'bg-white/5 text-blue-200 text-xs uppercase'}`}><tr><th className="p-4">Date</th><th className="p-4">Name</th><th className="p-4">Code</th><th className="p-4 text-right">Amount</th></tr></thead><tbody className={`divide-y ${highContrast ? 'divide-black bg-white text-black font-bold' : 'divide-white/5 text-sm'}`}>{data.map(d => (<tr key={d.id} className={highContrast ? 'hover:bg-gray-100' : 'hover:bg-white/5'}><td className="p-4">{new Date(d.date_added).toLocaleDateString()}</td><td className="p-4">{d.first_name} {d.second_name}</td><td className="p-4">{d.mpesa_code}</td><td className="p-4 text-right">{d.amount}</td></tr>))}</tbody></table></div></GlassCard>
        </div>
    )
}
