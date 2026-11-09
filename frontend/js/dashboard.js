"use strict";

/* CST Student Leave Management — framework-free dashboard.
   All data displayed here comes from the authenticated Flask API. */
const API = window.location.origin;
const AUTH_KEY = "slm_auth";
const $ = (selector) => document.querySelector(selector);
const state = {
  auth: null, user: null, page: "overview", leaves: [], summary: {},
  types: [], allTypes: [], users: [], notifications: [], unread: 0,
  search: "", filter: "all", editLeave: null, busy: false,
};

const ICONS = {
  overview: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
  leaves: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>',
  apply: '<path d="M12 20h9M16 3l5 5-12 12H4v-5L16 3Z"/>',
  review: '<path d="M4 5h16M4 12h10M4 19h8"/><circle cx="19" cy="17" r="3"/>',
  notifications: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>',
  users: '<circle cx="9" cy="8" r="3"/><path d="M3 20v-2a6 6 0 0 1 12 0v2M17 4a3 3 0 0 1 0 6M18 14a5 5 0 0 1 3 5"/>',
  types: '<path d="M20 12V4H4v16h8M8 8h8M8 12h5M8 16h3"/><path d="m16 18 2 2 4-4"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M4.9 4.9 7 7m10 10 2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrow: '<path d="M5 12h14m-6-6 6 6-6 6"/>',
  refresh: '<path d="M20 7v5h-5M4 17v-5h5"/><path d="M5.6 9a7 7 0 0 1 12-3l2.4 6M4 12l2.4 6a7 7 0 0 0 12-3"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>',
  edit: '<path d="M12 20h9M16 3l5 5-12 12H4v-5L16 3Z"/>',
  eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
};
function icon(key) { return `<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">${ICONS[key] || ICONS.leaves}</svg>`; }
function esc(value) { return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c])); }
function labelRole(role) { return ({student:"Student",faculty:"Faculty",admin:"Administrator"})[role] || role; }
function initials(name) { return String(name || "User").split(/\s+/).filter(Boolean).slice(0, 2).map(x=>x[0]).join("").toUpperCase(); }
function fmtDate(value) {
  if (!value) return "—";
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return esc(value);
  return new Date(+match[1], +match[2] - 1, +match[3]).toLocaleDateString("en-GB", {day:"numeric",month:"short",year:"numeric"});
}
function fmtTime(value) {
  if (!value) return "—";
  const date = new Date(String(value).replace(" ", "T") + (String(value).includes("Z") ? "" : ""));
  return Number.isNaN(date.getTime()) ? esc(value) : date.toLocaleString("en-GB", {day:"numeric",month:"short",year:"numeric",hour:"2-digit",minute:"2-digit"});
}
function today() { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`; }
function statusBadge(status) { return `<span class="status ${esc(status)}">${esc(status)}</span>`; }
function actionButton(action,label,id,css="btn-light",ico="") { return `<button type="button" class="btn btn-sm ${css}" data-action="${esc(action)}" data-id="${esc(id)}">${ico ? icon(ico) : ""}${esc(label)}</button>`; }
function getAuth() {
  for (const storage of [sessionStorage, localStorage]) {
    try { const auth=JSON.parse(storage.getItem(AUTH_KEY)||"null"); if (auth?.token) return auth; } catch (_) { storage.removeItem(AUTH_KEY); }
  }
  return null;
}
function signOut() { sessionStorage.removeItem(AUTH_KEY); localStorage.removeItem(AUTH_KEY); window.location.replace("/"); }
async function api(path, opts={}) {
  const headers = {Accept:"application/json", ...(opts.headers || {})};
  if (state.auth?.token) headers.Authorization = `Bearer ${state.auth.token}`;
  if (opts.body && !(opts.body instanceof FormData)) headers["Content-Type"] = "application/json";
  let response;
  try { response = await fetch(`${API}${path}`, {method:opts.method || "GET",headers,body:opts.body instanceof FormData ? opts.body : (opts.body ? JSON.stringify(opts.body) : undefined)}); }
  catch (_) { throw new Error("Cannot reach the server. Check that Flask and PostgreSQL are running."); }
  const data=await response.json().catch(()=>({}));
  if (!response.ok) {
    if (response.status===401 && !path.startsWith("/api/login")) { toast("Your session expired. Please sign in again.",true); setTimeout(signOut,900); }
    throw new Error(data.error || `Request failed (${response.status})`);
  }
  return data;
}
function toast(message,isError=false) {
  const root=$("#toastRoot"); root.innerHTML=`<div class="toast ${isError?"error":""}"><span>${esc(message)}</span><button aria-label="Dismiss message" type="button" data-action="toast-close">×</button></div>`;
  clearTimeout(toast.timer); toast.timer=setTimeout(()=>root.innerHTML="",5500);
}
function showError(message) { $("#mainContent").innerHTML=`<div class="panel"><div class="empty-state"><div class="empty-illustration">!</div><h3>Could not load this page</h3><p>${esc(message)}</p><div style="margin-top:20px"><button class="btn btn-primary" data-action="retry">Try again</button></div></div></div>`; }
function menuItems() {
  const nav=[{id:"overview",label:"Overview",icon:"overview"},{id:"leaves",label:state.user.role==="student"?"My applications":"All applications",icon:"leaves"}];
  if(state.user.role==="student") nav.push({id:"apply",label:"Apply for leave",icon:"apply"});
  if(state.user.role!=="student") nav.push({id:"review",label:"Pending approvals",icon:"review",count:state.summary.pending||0});
  if(state.user.role==="admin") nav.push({id:"users",label:"Manage users",icon:"users"},{id:"types",label:"Leave types",icon:"types"});
  nav.push({id:"notifications",label:"Notifications",icon:"notifications",count:state.unread},{id:"settings",label:"Account settings",icon:"settings"});
  return nav;
}
function renderSidebar() {
  $("#sideNav").innerHTML=menuItems().map(x=>`<button class="nav-link ${state.page===x.id?"active":""}" data-page="${x.id}" type="button">${icon(x.icon)}<span>${esc(x.label)}</span>${x.count?`<span class="nav-count">${x.count}</span>`:""}</button>`).join("");
  $("#headerAvatar").textContent=initials(state.user.name);
  $("#headerName").textContent=state.user.name;
  $("#headerRole").textContent=labelRole(state.user.role);
  $("#notificationDot").hidden=!state.unread;
  $("#breadcrumbText").textContent=menuItems().find(x=>x.id===state.page)?.label||"Overview";
}
function closeSidebar() {$("#sidebar").classList.remove("open");$("#sidebarShade").hidden=true;}
function header(kicker,title,description,buttons="") {return `<div class="page-header"><div><div class="eyebrow">${esc(kicker)}</div><h1>${esc(title)}</h1><p>${esc(description)}</p></div>${buttons?`<div class="header-tools">${buttons}</div>`:""}</div>`;}
function statCards(){const s=state.summary;return `<div class="stats-grid">${[
  ["Total requests",s.total||0,"leaves","All recorded applications",""],
  ["Pending review",s.pending||0,"clock","Awaiting a decision","pending"],
  ["Approved",s.approved||0,"check","Accepted applications","approved"],
  ["Rejected",s.rejected||0,"x","Declined applications","rejected"]
].map(([title,num,ic,note,cls])=>`<div class="stat-card ${cls}"><div class="stat-top"><span>${title}</span><span class="stat-icon">${icon(ic)}</span></div><div class="stat-number">${num}</div><div class="stat-note">${note}</div></div>`).join("")}</div>`;}
function recentTable(items,compact=false) {
  if(!items.length) return `<div class="table-empty">No leave applications found yet.</div>`;
  return `<div class="table-wrap"><table class="data-table"><thead><tr><th>Application</th>${state.user.role!=="student"?"<th>Student</th>":""}<th>Dates</th><th>Status</th><th>Action</th></tr></thead><tbody>${items.map(leave=>`<tr><td><strong>${esc(leave.leave_type)}</strong><span class="subtext">#${leave.id} · ${leave.total_days} day${leave.total_days===1?"":"s"}</span></td>${state.user.role!=="student"?`<td><strong>${esc(leave.student_name)}</strong><span class="subtext">${esc(leave.student_department||"No department")}</span></td>`:""}<td>${fmtDate(leave.start_date)}<span class="subtext">to ${fmtDate(leave.end_date)}</span></td><td>${statusBadge(leave.status)}</td><td><div class="table-actions">${actionButton("view","Details",leave.id,"btn-light","eye")}${!compact&&leave.status==="pending"&&state.user.role==="student"?actionButton("edit-leave","Edit",leave.id):""}${!compact&&leave.status==="pending"&&state.user.role!=="student"?actionButton("review-open","Review",leave.id,"btn-soft"):""}</div></td></tr>`).join("")}</tbody></table></div>`;
}
function renderOverview(){
  const user=state.user; const isStudent=user.role==="student";
  const action=isStudent?`<button class="btn hero-action" data-page="apply">${icon("plus")} New leave application</button>`:user.role==="admin"?`<button class="btn hero-action" data-page="review">Review pending requests ${icon("arrow")}</button>`:`<button class="btn hero-action" data-page="review">Review applications ${icon("arrow")}</button>`;
  const headline=isStudent?"Leave requests, made simple.":user.role==="faculty"?"Review requests with confidence.":"Keep your campus organized.";
  const desc=isStudent?"Apply for leave, check your decision and follow every update from one place.":user.role==="faculty"?"View requests from your department and respond to students promptly.":"Oversee leave requests, student accounts and leave policies for your college.";
  const hero=`<section class="overview-hero"><div><h2>${headline}</h2><p>${desc}</p></div>${action}</section>`;
  const recent=`<section class="panel"><div class="panel-head"><div><h2>Recent applications</h2><p>${isStudent?"Your latest leave requests":"Latest visible student requests"}</p></div><button class="text-link" data-page="leaves">View all →</button></div>${recentTable(state.leaves.slice(0,5),true)}</section>`;
  const max=Math.max(1,state.summary.total||0);
  const breakdown=`<section class="panel"><div class="panel-head"><div><h2>Application overview</h2><p>Current application status</p></div></div><div class="panel-body">${["pending","approved","rejected","cancelled"].map(s=>`<div class="breakdown-row"><span>${s[0].toUpperCase()+s.slice(1)}</span><b>${state.summary[s]||0}</b></div><div class="progress-track"><div class="progress-fill ${s}" style="width:${Math.round((state.summary[s]||0)/max*100)}%"></div></div>`).join("")}</div></section>`;
  const workflow=`<section class="panel"><div class="panel-head"><div><h2>${isStudent?"How it works":"Review workflow"}</h2><p>A simple, transparent process</p></div></div><div class="panel-body workflow">${(isStudent?[
    ["Complete an application","Choose a leave type, dates and reason."],
    ["Faculty reviews your request","Your department receives the application."],
    ["Follow your decision","Check the status and notifications anytime."]
  ]:[
    ["Check new submissions","Use Pending approvals to see awaiting requests."],
    ["Review supporting details","Open the reason, dates and any attachment."],
    ["Approve or reject","Students receive an in-app notification."]
  ]).map((x,i)=>`<div class="workflow-step"><span class="workflow-index">${i+1}</span><div><strong>${x[0]}</strong><p>${x[1]}</p></div></div>`).join("")}</div></section>`;
  const notice=`<section class="panel"><div class="panel-head"><div><h2>Latest notifications</h2><p>${state.unread} unread update${state.unread===1?"":"s"}</p></div><button class="text-link" data-page="notifications">View all →</button></div><div class="panel-body">${state.notifications.slice(0,3).map(n=>`<div class="workflow-step" style="padding:10px 0"><span class="workflow-index">${n.is_read?"✓":"!"}</span><div><strong>${esc(n.title)}</strong><p>${esc(n.message)}</p></div></div>`).join("")||"<span class='small-note'>No updates yet.</span>"}</div></section>`;
  $("#mainContent").innerHTML=header("Your workspace",`Hello, ${user.name.split(" ")[0]} 👋`,`${labelRole(user.role)} workspace · ${user.department||"College of Science and Technology"}`,`<button class="btn btn-light" data-action="refresh">${icon("refresh")} Refresh</button>`)+hero+statCards()+`<div class="content-grid"><div class="stack">${recent}${breakdown}</div><div class="stack">${workflow}${notice}</div></div>`;
}
function visibleLeaves(){const q=state.search.toLowerCase();return state.leaves.filter(l=>(state.filter==="all"||l.status===state.filter)&&(!q||[l.student_name,l.leave_type,l.reason,l.student_email,`#${l.id}`,l.student_department].some(v=>String(v||"").toLowerCase().includes(q))));}
function renderLeaves(){const list=visibleLeaves(); const title=state.user.role==="student"?"My leave applications":"All leave applications";
  $("#mainContent").innerHTML=header("Application records",title,`${state.leaves.length} leave request${state.leaves.length===1?"":"s"} accessible to your account`,state.user.role==="student"?`<button class="btn btn-primary" data-page="apply">${icon("plus")} Apply for leave</button>`:`<button class="btn btn-light" data-action="refresh">${icon("refresh")} Refresh</button>`)+`<section class="panel"><div class="section-filters"><label class="searchbox" aria-label="Search applications">${icon("search")}<input id="leaveSearch" placeholder="Search by student, type, reason..." value="${esc(state.search)}" /></label><select id="statusFilter" class="select-input" aria-label="Filter by status">${["all","pending","approved","rejected","cancelled"].map(s=>`<option value="${s}" ${state.filter===s?"selected":""}>${s==="all"?"All statuses":s[0].toUpperCase()+s.slice(1)}</option>`).join("")}</select></div><div id="leaveTableContainer">${renderLeaveRecords(list)}</div></section>`;
}
function renderLeaveRecords(list){
  if(!list.length) return `<div class="empty-state"><div class="empty-illustration">${icon("leaves")}</div><h3>No matching applications</h3><p>Try changing the search or status filter.</p>${state.user.role==="student"?`<div style="margin-top:19px"><button class="btn btn-primary" data-page="apply">Apply for leave</button></div>`:""}</div>`;
  return `<div class="table-wrap"><table class="data-table"><thead><tr><th>Request</th>${state.user.role!=="student"?"<th>Student</th>":""}<th>Leave period</th><th>Status</th><th>Submitted</th><th>Actions</th></tr></thead><tbody>${list.map(l=>`<tr><td><strong>${esc(l.leave_type)}</strong><span class="subtext">Request #${l.id} · ${l.total_days} day${l.total_days===1?"":"s"}</span></td>${state.user.role!=="student"?`<td><strong>${esc(l.student_name)}</strong><span class="subtext">${esc(l.student_department||"Unassigned")}</span></td>`:""}<td>${fmtDate(l.start_date)}<span class="subtext">${fmtDate(l.end_date)}</span></td><td>${statusBadge(l.status)}</td><td>${fmtDate(l.submitted_at)}</td><td><div class="table-actions">${actionButton("view","View",l.id,"btn-light","eye")}${state.user.role==="student"&&l.status==="pending"?actionButton("edit-leave","Edit",l.id,"btn-light","edit"):""}${state.user.role==="student"&&(l.status==="pending"||(l.status==="approved"&&l.start_date>today()))?actionButton("cancel-leave","Cancel",l.id,"btn-outline-danger"):""}${state.user.role!=="student"&&l.status==="pending"?actionButton("review-open","Review",l.id,"btn-soft"):""}</div></td></tr>`).join("")}</tbody></table></div><div style="padding:15px 20px;color:#97a5b5;font-size:11px">Showing ${list.length} of ${state.leaves.length} available applications</div>`;
}
function renderApply(){if(state.user.role!=="student")return navigate("overview");const edit=state.editLeave;
  const options=state.types.map(t=>`<option value="${t.id}" ${Number(edit?.leave_type_id)===t.id?"selected":""}>${esc(t.name)} (max ${t.max_days} days)${t.requires_doc?" · Document required":""}</option>`).join("");
  $("#mainContent").innerHTML=header("Student services",edit?"Edit leave request":"Apply for leave",edit?`Update pending request #${edit.id}`:"Complete the information below to submit a leave application.")+`<section class="panel form-panel"><div class="panel-head"><div><h2>${edit?"Update application":"Application details"}</h2><p>Fields marked * are required</p></div>${edit?statusBadge(edit.status):""}</div><div class="panel-body"><form id="leaveForm"><div class="form-fields"><label class="form-group full"><span class="form-label">Leave category <em>*</em></span><select class="form-input" id="leaveType" required><option value="">Select a leave category</option>${options}</select><span class="form-hint" id="leaveTypeHint">Medical and some academic categories require supporting evidence.</span></label><label class="form-group"><span class="form-label">Start date <em>*</em></span><input id="startDate" class="form-input" type="date" required value="${esc(edit?.start_date||"")}" /></label><label class="form-group"><span class="form-label">End date <em>*</em></span><input id="endDate" class="form-input" type="date" required value="${esc(edit?.end_date||"")}" /></label><label class="form-group full"><span class="form-label">Reason for leave <em>*</em></span><textarea id="leaveReason" class="form-input" rows="5" maxlength="2000" required placeholder="Briefly explain why you need leave...">${esc(edit?.reason||"")}</textarea><span class="form-hint">Please provide enough information for the reviewer to understand your request.</span></label><div class="form-group full"><label for="leaveAttachment" class="form-label">Supporting document (if required)</label><div class="upload-area"><input id="leaveAttachment" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" /><p class="form-hint">PDF, JPG or PNG · maximum 5 MB. Medical and Academic leave require an attachment.</p>${edit?.document_url?`<p class="form-hint">An attachment is already linked to this request. Leave this blank to keep it.</p>`:""}</div></div></div><div class="tip-box">${icon("calendar")} Applications are checked for overlapping dates. You can edit or cancel pending requests after submission.</div><div class="form-actions"><button type="button" class="btn btn-light" data-page="leaves">Cancel</button><button id="saveLeave" class="btn btn-primary" type="submit">${icon("check")} ${edit?"Save changes":"Submit application"}</button></div></form></div></section>`;
  updateTypeHint();
}
function updateTypeHint(){const type=state.types.find(t=>t.id===Number($("#leaveType")?.value));const hint=$("#leaveTypeHint");if(hint&&type)hint.textContent=`${type.name}: maximum ${type.max_days} day${type.max_days===1?"":"s"}.${type.requires_doc?" Supporting document required.":" Supporting document optional."}`;}
function renderReview(){if(state.user.role==="student")return navigate("overview");const pending=state.leaves.filter(l=>l.status==="pending");
  $("#mainContent").innerHTML=header("Faculty approvals","Pending approvals",`${pending.length} student request${pending.length===1?"":"s"} waiting for a decision`,`<button class="btn btn-light" data-action="refresh">${icon("refresh")} Refresh</button>`)+`<div class="panel"><div class="panel-head"><div><h2>Waiting for your review</h2><p>${state.user.role==="faculty"?`Only students in ${state.user.department||"your department"}`:"All campus departments"}</p></div></div>${pending.length?renderLeaveRecords(pending):`<div class="empty-state"><div class="empty-illustration">✓</div><h3>All caught up!</h3><p>There are no pending requests to review right now.</p></div>`}</div>`;
}
function renderNotifications(){
  $("#mainContent").innerHTML=header("Communication","Notifications",`${state.unread} unread notification${state.unread===1?"":"s"}`,`<button class="btn btn-light" data-action="read-all" ${state.unread?"":"disabled"}>${icon("check")} Mark all as read</button>`)+`<section class="panel">${state.notifications.length?state.notifications.map(n=>`<div class="notification-item ${n.is_read?"":"unread"}"><span class="notify-symbol">${n.type==="success"?"✓":n.type==="error"?"!":n.type==="warning"?"!":"✉"}</span><div><h3>${esc(n.title)}</h3><p>${esc(n.message)}</p><small>${fmtTime(n.created_at)}</small></div>${n.is_read?"":actionButton("read-one","Mark read",n.id)}</div>`).join(""):`<div class="empty-state"><div class="empty-illustration">✉</div><h3>No notifications yet</h3><p>Updates on your leave requests will appear here.</p></div>`}</section>`;
}
function renderUsers(){if(state.user.role!=="admin")return navigate("overview");
  $("#mainContent").innerHTML=header("Administration","User management",`${state.users.length} accounts registered`,`<button class="btn btn-primary" data-action="user-add">${icon("plus")} Add user</button>`)+`<section class="panel"><div class="section-filters"><label class="searchbox">${icon("search")}<input id="userSearch" placeholder="Search name, email, department..." value="${esc(state.search)}" /></label><select id="userRoleFilter" class="select-input"><option value="all">All roles</option>${["student","faculty","admin"].map(r=>`<option value="${r}" ${state.filter===r?"selected":""}>${labelRole(r)}</option>`).join("")}</select></div><div id="usersTable">${renderUsersTable()}</div></section>`;
}
function renderUsersTable(){const users=state.users.filter(u=>(state.filter==="all"||u.role===state.filter)&&(!state.search||[u.name,u.email,u.department,u.year].some(v=>String(v||"").toLowerCase().includes(state.search.toLowerCase()))));
  if(!users.length)return `<div class="table-empty">No matching users found.</div>`;
  return `<div class="table-wrap"><table class="data-table"><thead><tr><th>User</th><th>Role</th><th>Department</th><th>Year</th><th>Account</th><th>Action</th></tr></thead><tbody>${users.map(u=>`<tr><td><strong>${esc(u.name)}</strong><span class="subtext">${esc(u.email)}</span></td><td><span class="user-badge">${esc(u.role)}</span></td><td>${esc(u.department||"—")}</td><td>${esc(u.year||"—")}</td><td><span class="status ${u.is_active?"approved":"rejected"}">${u.is_active?"Active":"Inactive"}</span></td><td>${actionButton("user-edit","Edit",u.id)}</td></tr>`).join("")}</tbody></table></div>`;
}
function renderTypes(){if(state.user.role!=="admin")return navigate("overview");
  $("#mainContent").innerHTML=header("Administration","Leave categories","Configure leave duration, documents and availability.",`<button class="btn btn-primary" data-action="type-add">${icon("plus")} Add category</button>`)+`<section class="panel"><div class="table-wrap"><table class="data-table"><thead><tr><th>Category</th><th>Maximum days</th><th>Document</th><th>Status</th><th>Action</th></tr></thead><tbody>${state.allTypes.map(t=>`<tr><td><strong>${esc(t.name)}</strong><span class="subtext">${esc(t.description||"No description")}</span></td><td>${t.max_days} days</td><td>${t.requires_doc?"Required":"Optional"}</td><td><span class="status ${t.is_active?"approved":"cancelled"}">${t.is_active?"Active":"Inactive"}</span></td><td>${actionButton("type-edit","Edit",t.id)}</td></tr>`).join("")}</tbody></table></div></section>`;
}
function renderSettings(){const u=state.user;
  $("#mainContent").innerHTML=header("My account","Account settings","Your profile details and sign-in security.")+`<div class="profile-grid"><section class="panel"><div class="panel-head"><div><h2>Account information</h2><p>Managed by the college administrator</p></div></div><div class="panel-body detail-list">${[["Full name",u.name],["Email",u.email],["Account role",labelRole(u.role)],["Department",u.department||"Not assigned"],["Year of study",u.year||"—"],["Phone",u.phone||"Not provided"]].map(([k,v])=>`<div class="detail-item"><small>${esc(k)}</small><strong>${esc(v)}</strong></div>`).join("")}</div></section><section class="panel"><div class="panel-head"><div><h2>Change password</h2><p>Use at least 8 characters for your new password</p></div></div><div class="panel-body"><form id="passwordForm" class="form-fields" style="grid-template-columns:1fr"><label class="form-group"><span class="form-label">Current password</span><input id="currentPassword" type="password" autocomplete="current-password" class="form-input" required /></label><label class="form-group"><span class="form-label">New password</span><input id="newPassword" type="password" minlength="8" autocomplete="new-password" class="form-input" required /></label><label class="form-group"><span class="form-label">Confirm new password</span><input id="confirmPassword" type="password" minlength="8" autocomplete="new-password" class="form-input" required /></label><button type="submit" class="btn btn-primary">Update password</button></form><div class="tip-box">Your password is never displayed or stored by the frontend.</div></div></section></div>`;
}
function render(){renderSidebar();switch(state.page){case"overview":renderOverview();break;case"leaves":renderLeaves();break;case"apply":renderApply();break;case"review":renderReview();break;case"notifications":renderNotifications();break;case"users":renderUsers();break;case"types":renderTypes();break;case"settings":renderSettings();break;default:renderOverview();}}
function navigate(page){if(page!=="apply")state.editLeave=null;state.page=page;state.search="";state.filter="all";closeSidebar();render();window.scrollTo({top:0,behavior:"instant"});}
async function refresh(showToast=false){
  const calls=[api("/api/leaves?limit=500"),api("/api/leaves/summary"),api("/api/leave-types"),api("/api/notifications?limit=200")];
  if(state.user.role==="admin")calls.push(api("/api/users"),api("/api/leave-types?include_inactive=true"));
  const result=await Promise.all(calls);
  state.leaves=result[0].leaves;state.summary=result[1].summary;state.types=result[2].leave_types;state.notifications=result[3].notifications;state.unread=result[3].unread_count;
  if(state.user.role==="admin"){state.users=result[4].users;state.allTypes=result[5].leave_types;}
  render();if(showToast)toast("Your workspace is up to date.");
}
function modal(title,subtitle,body,actions){$("#modalRoot").innerHTML=`<div class="modal-backdrop" id="modalBackdrop" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="modalTitle" class="modal"><div class="modal-top"><div><h2 id="modalTitle">${esc(title)}</h2><p>${esc(subtitle)}</p></div><button type="button" class="close-modal" aria-label="Close" data-action="modal-close">×</button></div><div class="modal-body">${body}</div><div class="modal-actions">${actions}</div></section></div>`;$("#modalBackdrop .close-modal").focus();}
function closeModal(){$("#modalRoot").innerHTML="";}
function getLeave(id){return state.leaves.find(l=>l.id===Number(id));}
function viewLeave(id){const l=getLeave(id);if(!l)return toast("Request no longer exists",true);
  const fields=[["Leave type",l.leave_type],["Application status",l.status],["Start date",fmtDate(l.start_date)],["End date",fmtDate(l.end_date)],["Total duration",`${l.total_days} day${l.total_days===1?"":"s"}`],["Submitted",fmtTime(l.submitted_at)],["Student",l.student_name],["Department",l.student_department||"—"],["Reviewed by",l.reviewer_name||"Not yet reviewed"],["Review date",fmtTime(l.reviewed_at)]];
  const content=`<div class="detail-modal">${fields.map(([k,v])=>`<div><span class="form-label">${esc(k)}</span><p>${esc(v)}</p></div>`).join("")}<div class="wide"><span class="form-label">Reason</span><p class="reason">${esc(l.reason)}</p></div>${l.reviewer_comment?`<div class="wide"><span class="form-label">Reviewer comment</span><p class="reason">${esc(l.reviewer_comment)}</p></div>`:""}${l.document_url?`<div class="wide"><span class="form-label">Supporting document</span><button type="button" class="btn btn-light" data-action="document" data-id="${l.id}">View / download attachment</button></div>`:""}</div>`;
  modal(`Leave request #${id}`,"Application details",content,`<button class="btn btn-light" data-action="modal-close">Close</button>${state.user.role!=="student"&&l.status==="pending"?actionButton("review-open","Review request",l.id,"btn-primary"):""}`);
}
function openReview(id){const l=getLeave(id);if(!l||l.status!=="pending")return toast("This request is no longer pending.",true);
  modal(`Review leave #${l.id}`,`${l.student_name} · ${l.student_department||"No department"}`,`<div class="detail-modal"><div><span class="form-label">Leave category</span><p>${esc(l.leave_type)}</p></div><div><span class="form-label">Date range</span><p>${fmtDate(l.start_date)} – ${fmtDate(l.end_date)}</p></div><div class="wide"><span class="form-label">Reason</span><p class="reason">${esc(l.reason)}</p></div>${l.document_url?`<div class="wide"><button class="btn btn-light" type="button" data-action="document" data-id="${l.id}">View supporting document</button></div>`:""}<label class="form-group wide"><span class="form-label">Review comment (required if rejecting)</span><textarea class="form-input" rows="3" id="reviewComment" placeholder="Add a comment for the student..."></textarea></label></div>`,`<button class="btn btn-light" data-action="modal-close">Cancel</button><button class="btn btn-outline-danger" data-action="submit-review" data-id="${l.id}" data-decision="reject">Reject</button><button class="btn btn-primary" data-action="submit-review" data-id="${l.id}" data-decision="approve">${icon("check")} Approve</button>`);
}
function openUser(id){const u=id?state.users.find(x=>x.id===Number(id)):null;
  const years=["1st Year","2nd Year","3rd Year","4th Year","Final Year"];
  modal(u?"Edit user":"Add a user",u?`${u.email} · ${labelRole(u.role)}`:"Create an account for a student, faculty member or administrator",`<form id="userForm"><input type="hidden" name="id" value="${esc(u?.id||"")}"/><div class="form-fields"><label class="form-group"><span class="form-label">Full name *</span><input class="form-input" name="name" required maxlength="100" value="${esc(u?.name||"")}"/></label><label class="form-group"><span class="form-label">Department</span><input class="form-input" name="department" maxlength="100" value="${esc(u?.department||"")}"/></label>${u?`<div class="form-group"><span class="form-label">Email (cannot change)</span><input class="form-input" disabled value="${esc(u.email)}" /></div><div class="form-group"><span class="form-label">Role (cannot change)</span><input class="form-input" disabled value="${esc(labelRole(u.role))}" /></div>`:`<label class="form-group"><span class="form-label">Email *</span><input class="form-input" type="email" name="email" required maxlength="100" placeholder="name@cst.edu.bt" /></label><label class="form-group"><span class="form-label">Role *</span><select class="form-input" name="role" id="newUserRole"><option value="student">Student</option><option value="faculty">Faculty</option><option value="admin">Administrator</option></select></label>`}<label class="form-group" id="userYearGroup" ${u&&u.role!=="student"?"hidden":""}><span class="form-label">Academic year *</span><select class="form-input" name="year"><option value="">Select year</option>${years.map(y=>`<option value="${esc(y)}" ${u?.year===y?"selected":""}>${esc(y)}</option>`).join("")}</select></label><label class="form-group"><span class="form-label">Phone</span><input class="form-input" name="phone" maxlength="20" value="${esc(u?.phone||"")}" /></label><label class="form-group full"><span class="form-label">${u?"New password (leave empty to keep)":"Initial password *"}</span><input class="form-input" name="password" type="password" minlength="8" ${u?"":"required"} autocomplete="new-password" placeholder="At least 8 characters" /></label>${u?`<label class="checkline full"><input type="checkbox" name="is_active" ${u.is_active?"checked":""}/> Account active</label>`:""}</div></form>`,`<button class="btn btn-light" data-action="modal-close">Cancel</button><button class="btn btn-primary" data-action="user-save">${u?"Save changes":"Create user"}</button>`);
}
function openType(id){const t=id?state.allTypes.find(x=>x.id===Number(id)):null;
  modal(t?"Edit leave category":"New leave category",t?"Manage category rules":"Create a type of leave for students",`<form id="typeForm"><input type="hidden" name="id" value="${esc(t?.id||"")}"/><div class="form-fields"><label class="form-group"><span class="form-label">Name *</span><input class="form-input" name="name" maxlength="50" required value="${esc(t?.name||"")}" /></label><label class="form-group"><span class="form-label">Maximum days *</span><input type="number" class="form-input" min="1" max="365" name="max_days" required value="${esc(t?.max_days??30)}" /></label><label class="form-group full"><span class="form-label">Description</span><textarea class="form-input" name="description" rows="3">${esc(t?.description||"")}</textarea></label><label class="checkline"><input type="checkbox" name="requires_doc" ${t?.requires_doc?"checked":""} /> Require supporting document</label><label class="checkline"><input type="checkbox" name="is_active" ${!t||t.is_active?"checked":""} /> Category active</label></div></form>`,`<button class="btn btn-light" data-action="modal-close">Cancel</button><button class="btn btn-primary" data-action="type-save">${t?"Save changes":"Create category"}</button>`);
}
async function saveLeave(e){e.preventDefault();if(state.busy)return;
  const type=state.types.find(x=>x.id===Number($("#leaveType").value));const start=$("#startDate").value;const end=$("#endDate").value;const reason=$("#leaveReason").value.trim();const file=$("#leaveAttachment").files[0];
  if(!type)return toast("Choose a leave category.",true);if(!start||!end||start>end)return toast("Enter a valid date range.",true);
  if(!reason)return toast("Please explain the reason for leave.",true);
  if(type.requires_doc&&!file&&!state.editLeave?.document_url)return toast("This category requires a supporting document.",true);
  if(file&&file.size>5*1024*1024)return toast("Attachments cannot exceed 5 MB.",true);
  const btn=$("#saveLeave");state.busy=true;btn.disabled=true;btn.textContent="Submitting…";
  try{
    let document_url=state.editLeave?.document_url||null;
    if(file){const form=new FormData();form.append("file",file);const result=await api("/api/attachments",{method:"POST",body:form});document_url=result.document_url;}
    const payload={leave_type_id:type.id,reason,start_date:start,end_date:end,document_url};
    const edit=state.editLeave;
    await api(edit?`/api/leaves/${edit.id}`:"/api/leaves",{method:edit?"PUT":"POST",body:payload});
    state.editLeave=null;await refresh();navigate("leaves");toast(edit?"Leave application updated.":"Leave application submitted successfully.");
  }catch(error){toast(error.message,true);}finally{state.busy=false;const now=$("#saveLeave");if(now)now.disabled=false;}
}
async function savePassword(e){e.preventDefault();const current=$("#currentPassword").value;const next=$("#newPassword").value;const confirm=$("#confirmPassword").value;
  if(next!==confirm)return toast("New passwords do not match.",true);if(next.length<8)return toast("Password must be at least 8 characters.",true);
  try{await api("/api/me/password",{method:"POST",body:{current_password:current,new_password:next}});$("#passwordForm").reset();toast("Password updated successfully.");}catch(error){toast(error.message,true);}
}
async function saveUser(){const form=$("#userForm");if(!form.reportValidity())return;const d=new FormData(form);const id=Number(d.get("id"));let payload;
  if(id){payload={name:String(d.get("name")).trim(),department:d.get("department"),phone:d.get("phone"),is_active:d.has("is_active")};const u=state.users.find(x=>x.id===id);if(u.role==="student")payload.year=d.get("year");if(d.get("password"))payload.password=d.get("password");}
  else {payload={name:String(d.get("name")).trim(),email:String(d.get("email")).trim(),role:d.get("role"),department:d.get("department"),phone:d.get("phone"),password:d.get("password")};if(payload.role==="student")payload.year=d.get("year");}
  try{await api(id?`/api/users/${id}`:"/api/users",{method:id?"PUT":"POST",body:payload});closeModal();await refresh();toast(id?"User updated.":"User created.");}catch(e){toast(e.message,true);}
}
async function saveType(){const form=$("#typeForm");if(!form.reportValidity())return;const d=new FormData(form);const id=Number(d.get("id"));const payload={name:d.get("name"),description:d.get("description"),max_days:Number(d.get("max_days")),requires_doc:d.has("requires_doc"),is_active:d.has("is_active")};
  try{await api(id?`/api/leave-types/${id}`:"/api/leave-types",{method:id?"PUT":"POST",body:payload});closeModal();await refresh();toast(id?"Category updated.":"Leave category created.");}catch(e){toast(e.message,true);}
}
async function documentDownload(id){const l=getLeave(id);if(!l?.document_url)return;
  if(l.document_url.startsWith("https://")){window.open(l.document_url,"_blank","noopener,noreferrer");return;}
  try{const r=await fetch(`${API}${l.document_url}`,{headers:{Authorization:`Bearer ${state.auth.token}`}});if(!r.ok)throw new Error("Document unavailable or access denied.");const blob=await r.blob();const link=document.createElement("a");link.href=URL.createObjectURL(blob);link.download=`leave-${l.id}-attachment.${l.document_url.split(".").pop()||"pdf"}`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),3000);}
  catch(e){toast(e.message,true);}
}
async function runAction(button){const type=button.dataset.action;const id=button.dataset.id;
  if(type==="modal-close")return closeModal();if(type==="toast-close"){ $("#toastRoot").innerHTML="";return; }
  if(type==="view")return viewLeave(id);
  if(type==="review-open")return openReview(id);
  if(type==="edit-leave"){state.editLeave=getLeave(id);return navigate("apply");}
  if(type==="document")return documentDownload(id);
  if(type==="user-add")return openUser(null);if(type==="user-edit")return openUser(id);if(type==="type-add")return openType(null);if(type==="type-edit")return openType(id);
  if(type==="user-save")return saveUser();if(type==="type-save")return saveType();
  if(type==="retry"||type==="refresh"){try{await refresh(true)}catch(e){showError(e.message)}return;}
  if(type==="cancel-leave"){if(!confirm(`Cancel leave request #${id}? This cannot be undone.`))return;try{await api(`/api/leaves/${id}/cancel`,{method:"POST"});await refresh();toast("Request cancelled.");}catch(e){toast(e.message,true);}return;}
  if(type==="submit-review"){
    const action=button.dataset.decision;const comment=$("#reviewComment")?.value.trim()||"";
    if(action==="reject"&&!comment)return toast("Please provide a reason when rejecting.",true);
    try{button.disabled=true;await api(`/api/leaves/${id}/review`,{method:"POST",body:{action,comment}});closeModal();await refresh();toast(`Request ${action==="approve"?"approved":"rejected"}. The student was notified.`);}catch(e){button.disabled=false;toast(e.message,true);}return;
  }
  if(type==="read-one"){try{await api(`/api/notifications/${id}/read`,{method:"POST"});await refresh();}catch(e){toast(e.message,true);}return;}
  if(type==="read-all"){try{await api("/api/notifications/read-all",{method:"POST"});await refresh();toast("All notifications marked read.");}catch(e){toast(e.message,true);}}
}

document.addEventListener("click",async e=>{
  const nav=e.target.closest("[data-page]");if(nav){navigate(nav.dataset.page);return;}
  const action=e.target.closest("[data-action]");if(action){e.preventDefault();await runAction(action);return;}
  if(e.target.id==="modalBackdrop")closeModal();
});
document.addEventListener("submit",async e=>{if(e.target.id==="leaveForm")await saveLeave(e);else if(e.target.id==="passwordForm")await savePassword(e);});
document.addEventListener("input",e=>{
  if(e.target.id==="leaveSearch"){state.search=e.target.value;const el=$("#leaveTableContainer");if(el)el.innerHTML=renderLeaveRecords(visibleLeaves());}
  if(e.target.id==="userSearch"){state.search=e.target.value;$("#usersTable").innerHTML=renderUsersTable();}
});
document.addEventListener("change",e=>{
  if(e.target.id==="statusFilter"){state.filter=e.target.value;$("#leaveTableContainer").innerHTML=renderLeaveRecords(visibleLeaves());}
  if(e.target.id==="userRoleFilter"){state.filter=e.target.value;$("#usersTable").innerHTML=renderUsersTable();}
  if(e.target.id==="leaveType")updateTypeHint();
  if(e.target.id==="newUserRole")$("#userYearGroup").hidden=e.target.value!=="student";
});
document.addEventListener("keydown",e=>{if(e.key==="Escape")closeModal();});
$("#menuToggle").addEventListener("click",()=>{$("#sidebar").classList.toggle("open");$("#sidebarShade").hidden=!$("#sidebar").classList.contains("open");});
$("#sidebarShade").addEventListener("click",closeSidebar);
$("#logoutButton").addEventListener("click",signOut);
$("#accountButton").addEventListener("click",()=>navigate("settings"));
$("#notificationButton").addEventListener("click",()=>navigate("notifications"));

(async()=>{
  state.auth=getAuth();if(!state.auth)return signOut();
  try{const data=await api("/api/me");state.user=data.user;await refresh();}
  catch(e){if(!state.user)signOut();else showError(e.message);}
})();
