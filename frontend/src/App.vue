<template>
  <div class="flex flex-col items-center justify-center min-h-screen p-4 bg-gray-900 relative">
    
    <div v-if="lightboxVisible" @click="lightboxVisible = false" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 cursor-zoom-out backdrop-blur-sm transition-opacity">
      <img :src="resolveAvatar(lightboxUrl)" class="max-w-[90vw] max-h-[90vh] rounded-lg shadow-[0_0_50px_rgba(0,0,0,0.8)] object-contain border border-gray-700" @click.stop>
      <button @click="lightboxVisible = false" class="absolute top-6 right-6 text-white bg-gray-800 hover:bg-gray-700 rounded-full w-10 h-10 flex items-center justify-center font-bold text-xl transition">×</button>
    </div>

    <div v-if="isLoggedIn" class="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      <transition name="fade-slide">
        <div v-if="chatOpen" class="w-80 sm:w-96 h-[30rem] bg-gray-900 border border-gray-600 rounded-xl shadow-[0_0_30px_rgba(0,0,0,0.8)] flex flex-col overflow-hidden mb-4">
          <div class="bg-gray-800 p-3 border-b border-gray-700 flex justify-between items-center shadow-md z-10">
            <span class="text-sm font-bold text-gray-200 flex items-center"><span class="mr-2">📡</span> 幻想乡频道</span>
            <button @click="toggleChat" class="text-gray-400 hover:text-red-400 font-bold text-lg transition px-2">×</button>
          </div>
          <div ref="chatBoxRef" class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900/80 scroll-smooth custom-scrollbar">
            <div v-if="chatMessages.length === 0" class="text-center text-xs text-gray-600 mt-10">频道很安静，来说点什么吧...</div>
            
            <div v-for="msg in chatMessages" :key="msg.id" class="flex flex-col" :class="msg.sender_name === userInfo.username ? 'items-end' : 'items-start'">
              <span class="text-[10px] text-gray-500 mb-1 flex items-center">
                <span v-if="msg.is_admin && msg.sender_name !== userInfo.username" class="text-indigo-400 mr-1">👑</span>
                {{ msg.sender_name }}
              </span>
              <div class="flex items-end gap-2" :class="msg.sender_name === userInfo.username ? 'flex-row-reverse' : 'flex-row'">
                <img @click="openLightbox(msg.sender_avatar)" :src="resolveAvatar(msg.sender_avatar)" class="w-8 h-8 rounded-full border border-gray-600 object-cover cursor-zoom-in hover:border-blue-400 transition shrink-0" />
                <div class="relative group/bubble">
                  <button v-if="userInfo.is_admin" @click="deleteChatMessage(msg.id)" 
                          class="absolute -top-2 -right-2 bg-red-600 hover:bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] opacity-0 group-hover/bubble:opacity-100 transition shadow-lg z-10"
                          title="删除消息">✕</button>
                  <div class="px-3 py-2 rounded-lg text-sm max-w-[200px] break-words shadow-md"
                       :class="msg.sender_name === userInfo.username ? 'bg-blue-600 text-white rounded-br-none' : 'bg-gray-700 text-gray-200 rounded-bl-none'">
                    {{ msg.content }}
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="p-3 bg-gray-800 border-t border-gray-700 flex gap-2">
            <input v-model="newChatMessage" @keyup.enter="sendChatMessage" type="text" placeholder="按回车发送..." class="flex-1 bg-gray-900 text-white rounded px-3 py-2 border border-gray-600 text-sm focus:border-blue-500 outline-none">
            <button @click="sendChatMessage" class="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded transition text-sm">发送</button>
          </div>
        </div>
      </transition>

      <button @click="toggleChat" class="bg-blue-600 hover:bg-blue-500 rounded-full w-14 h-14 flex items-center justify-center text-2xl shadow-[0_0_20px_rgba(37,99,235,0.6)] hover:scale-110 transition-transform relative">
        💬
        <span v-if="unreadCount > 0" class="absolute -top-1 -right-1 bg-red-500 border-2 border-gray-900 text-white text-xs font-bold rounded-full h-6 min-w-[24px] flex items-center justify-center px-1 animate-bounce">
          {{ unreadCount > 99 ? '99+' : unreadCount }}
        </span>
      </button>
    </div>

    <div class="max-w-3xl w-full bg-gray-800 rounded-xl shadow-2xl overflow-hidden border border-gray-700">
      
      <div class="bg-gray-900 p-4 border-b border-gray-700 flex justify-between items-center">
        <h1 class="text-xl font-bold text-gray-100 flex items-center"><span class="mr-2">🏛️</span> 幻想乡投票终端</h1>
        <div class="flex items-center space-x-4">
          <button v-if="isLoggedIn" @click="logout" class="text-sm text-gray-400 hover:text-white transition">登出</button>
          <div class="flex items-center space-x-2">
            <span class="relative flex h-3 w-3"><span :class="wsConnected ? 'bg-green-400 animate-ping absolute inline-flex h-full w-full rounded-full opacity-75' : ''"></span><span :class="wsConnected ? 'bg-green-500' : 'bg-red-500'" class="relative inline-flex rounded-full h-3 w-3"></span></span>
            <span class="text-xs text-gray-400">{{ wsConnected ? '连接正常' : '信号丢失' }}</span>
          </div>
        </div>
      </div>

      <div v-if="!isLoggedIn" class="p-8">
        <div class="flex justify-center mb-6 space-x-4">
          <button @click="authMode = 'login'" :class="authMode === 'login' ? 'text-white border-b-2 border-blue-500' : 'text-gray-500'" class="text-xl font-bold pb-1 transition">入会认证</button>
          <button @click="authMode = 'register'" :class="authMode === 'register' ? 'text-white border-b-2 border-green-500' : 'text-gray-500'" class="text-xl font-bold pb-1 transition">申请入会</button>
        </div>
        <div class="space-y-4 max-w-sm mx-auto">
          <input v-model="authForm.username" @keyup.enter="authMode === 'login' ? handleLogin() : handleRegister()" type="text" placeholder="委员账号" class="w-full bg-gray-700 text-white rounded px-4 py-2 border border-gray-600 focus:outline-none focus:border-blue-500">
          <input v-model="authForm.password" @keyup.enter="authMode === 'login' ? handleLogin() : handleRegister()" type="password" placeholder="密码" class="w-full bg-gray-700 text-white rounded px-4 py-2 border border-gray-600 focus:outline-none focus:border-blue-500">
          <input v-if="authMode === 'register'" v-model="authForm.confirmPassword" @keyup.enter="handleRegister" type="password" placeholder="确认密码" class="w-full bg-gray-700 text-white rounded px-4 py-2 border border-gray-600 focus:outline-none focus:border-green-500">
          <button v-if="authMode === 'login'" @click="handleLogin" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded transition">登 入</button>
          <button v-if="authMode === 'register'" @click="handleRegister" class="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-2 px-4 rounded transition">提交入会申请</button>
          <p class="text-center text-sm" :class="sysMsg.includes('成功') || sysMsg.includes('提交') ? 'text-green-400' : 'text-red-400'">{{ sysMsg || errorMessage }}</p>
        </div>
      </div>

      <div v-else class="flex flex-col">
        <div class="bg-gray-800 border-b border-gray-700 flex">
          <button @click="activeMainTab = 'vote'" :class="activeMainTab === 'vote' ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-gray-200'" class="flex-1 py-3 border-b-2 font-bold transition relative flex justify-center items-center">
            当前决选
            <span v-if="userInfo.is_admin && pendingCount > 0" class="absolute top-3 right-4 sm:right-8 flex h-2.5 w-2.5">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
            </span>
          </button>
          <button @click="fetchHistory(); activeMainTab = 'history'" :class="activeMainTab === 'history' ? 'border-blue-500 text-blue-400' : 'border-transparent text-gray-400 hover:text-gray-200'" class="flex-1 py-3 border-b-2 font-bold transition">历史档案</button>
          <button @click="fetchMyVotes(); activeMainTab = 'profile'" :class="activeMainTab === 'profile' ? 'border-purple-500 text-purple-400' : 'border-transparent text-gray-400 hover:text-gray-200'" class="flex-1 py-3 border-b-2 font-bold transition">个人中心</button>
        </div>

        <div class="relative transition-[height] duration-500 ease-[cubic-bezier(0.25,1,0.265,1.15)] overflow-hidden" :style="{ height: containerHeight }">
          <transition 
            name="tab-fade" 
            @before-leave="onBeforeLeave"
            @enter="onEnter"
            @after-enter="onAfterEnter"
          >
            <div :key="activeMainTab" class="w-full flex flex-col">

                <div v-if="userInfo.is_admin && activeMainTab === 'vote'" class="bg-indigo-900/40 border-b border-indigo-700 p-5">
                  <div class="flex items-center justify-between mb-4"><h2 class="text-indigo-300 font-bold flex items-center text-lg"><span class="mr-2">⚙️</span> 系统总控台</h2><div class="space-x-2"><button @click="activeAdminTab = 'election'" :class="activeAdminTab === 'election' ? 'bg-indigo-600 text-white' : 'bg-indigo-800 text-indigo-300 hover:bg-indigo-700'" class="px-3 py-1 rounded text-sm transition">选举控制</button><button @click="fetchUserList(); activeAdminTab = 'users'" :class="activeAdminTab === 'users' ? 'bg-indigo-600 text-white' : 'bg-indigo-800 text-indigo-300 hover:bg-indigo-700'" class="px-3 py-1 rounded text-sm transition relative">人员管理<span v-if="pendingCount > 0" class="absolute -top-1 -right-1 flex h-3 w-3"><span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span><span class="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span></span></button></div></div>
                  <div v-if="activeAdminTab === 'election'" class="flex space-x-3"><button @click="adminStartElection" class="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-2 rounded transition text-sm">🚀 开启/重置本月选举</button><button v-if="electionInfo.status === 'voting'" @click="adminTallyRound" class="flex-1 bg-pink-600 hover:bg-pink-500 text-white font-bold py-2 rounded transition shadow-[0_0_10px_rgba(219,39,119,0.5)] text-sm">⚡ 结算当前轮次</button><button v-if="electionInfo.status === 'completed'" @click="adminArchive" class="flex-1 bg-gray-600 hover:bg-gray-500 text-white font-bold py-2 rounded transition text-sm">📁 关闭大结局</button></div>
                  <div v-if="activeAdminTab === 'users'" class="space-y-4">
                    <div class="max-h-48 overflow-y-auto border border-indigo-700 rounded bg-gray-900/50 p-2 custom-scrollbar"><div v-for="u in userList" :key="u.id" class="flex justify-between items-center py-2 border-b border-indigo-800/50 last:border-0 text-sm"><div><span v-if="u.is_admin" class="text-indigo-400 mr-1">👑</span><span :class="u.is_approved ? 'text-gray-200' : 'text-gray-500 line-through decoration-red-500'">{{ u.username }}</span><span v-if="!u.is_approved" class="ml-2 text-xs bg-red-900/50 text-red-400 px-1 rounded animate-pulse">待审批</span></div><div v-if="!u.is_admin" class="space-x-2"><button v-if="!u.is_approved" @click="adminApproveUser(u)" class="text-xs bg-green-600 hover:bg-green-500 text-white px-2 py-1 rounded shadow-[0_0_8px_rgba(22,163,74,0.6)]">批准</button><button v-if="u.is_approved" @click="adminResetPassword(u)" class="text-xs bg-yellow-600 hover:bg-yellow-500 text-white px-2 py-1 rounded">改密</button><button @click="adminDeleteUser(u)" class="text-xs bg-red-600 hover:bg-red-500 text-white px-2 py-1 rounded">除名</button></div></div></div>
                  </div>
                </div>
    
                <div v-if="activeMainTab === 'vote'" class="p-6">
                  <div v-if="electionInfo.status === 'idle'" class="bg-gray-800 border border-gray-700 p-10 rounded-xl text-center shadow-inner"><div class="text-4xl mb-4">🔮</div><h2 class="text-xl text-gray-300 mb-2">当前处于休会期</h2><p class="text-sm text-gray-500 mb-6">下一次大选将于本月最后一日 16:00 准时开启</p><div class="inline-block bg-black/50 border border-blue-900 px-6 py-4 rounded-lg min-w-[300px]"><div class="text-xs text-blue-400 mb-1 font-bold tracking-widest uppercase">距离下次决选倒计时</div><div class="text-2xl font-mono text-white font-bold tracking-wider">{{ nextElectionCountdown || '计算中...' }}</div></div></div>
                  <div v-else class="flex flex-col items-center justify-center mb-8 border-b border-gray-700 pb-6 relative"><div class="absolute top-0 right-0 text-xs text-blue-400 font-mono bg-blue-900/30 px-2 py-1 rounded border border-blue-800/50">T+ {{ Math.floor(electionElapsedSeconds / 60) }}m {{ (electionElapsedSeconds % 60).toString().padStart(2, '0') }}s</div><div class="relative w-32 h-32 rounded-full border-4 border-gray-700 shadow-[0_0_20px_rgba(0,0,0,0.5)] flex items-center justify-center bg-gray-900 overflow-hidden"><div class="absolute inset-0 rounded-full opacity-40" style="background: conic-gradient(from 0deg, #2563eb 0deg 60deg, #d97706 60deg 90deg, #2563eb 90deg 150deg, #d97706 150deg 180deg, #2563eb 180deg 240deg, #d97706 240deg 270deg, #2563eb 270deg 330deg, #d97706 330deg 360deg);"></div><div class="absolute inset-0 rounded-full border-[8px] border-gray-800/80"></div><div class="absolute w-3 h-3 bg-white rounded-full z-20 shadow-lg"></div><div class="absolute w-1.5 h-12 bg-white rounded-full z-10 origin-bottom transition-transform duration-1000 ease-linear" :style="{ transform: `translateY(-50%) rotate(${progressDeg}deg)` }"></div><div class="absolute w-[1px] h-14 bg-red-500 z-10 origin-bottom transition-transform duration-1000 ease-linear" :style="{ transform: `translateY(-50%) rotate(${secondDeg}deg)` }"></div></div></div>
                  <div v-if="electionInfo.status === 'tallying'" class="bg-yellow-900/30 border border-yellow-600 p-6 rounded-lg text-center text-yellow-500 animate-pulse">⏳ 绝赞计票中，请等待最新公示...</div>
                  <div v-else-if="electionInfo.status === 'completed'" class="bg-gradient-to-b from-yellow-900/40 to-gray-800 border border-yellow-600 p-8 rounded-lg text-center shadow-[0_0_30px_rgba(202,138,4,0.2)]"><h2 class="text-3xl font-bold text-yellow-500 mb-2">本月大选圆满结束</h2><div class="text-6xl my-4">🏆</div><p class="text-gray-300 text-lg mb-6">新一任委员长是：<span class="text-2xl font-bold text-white ml-2">{{ electionInfo.winner?.username || '神秘人' }}</span></p><div class="bg-black/40 rounded p-4 text-left"><h3 class="text-sm text-gray-400 mb-3 border-b border-gray-700 pb-2">第四轮决选最终得票：</h3><div v-for="t in electionInfo.final_tally" :key="t.username" class="flex justify-between text-gray-200 mb-1"><span>{{ t.username }}</span><span class="font-bold text-yellow-500">{{ t.vote_count }} 票</span></div></div></div>
                  <div v-else-if="electionInfo.status === 'voting'" class="space-y-6">
                    <div v-if="electionInfo.round_number > 1" class="bg-blue-900/10 border border-blue-800 p-5 rounded-lg text-sm"><h3 class="text-blue-400 font-bold mb-3 flex items-center"><span class="mr-2">📊</span> 上一轮战况公示：</h3><div class="flex items-start mb-3"><span class="text-green-400 font-bold w-16 shrink-0 mt-1">✅ 晋级</span><div class="flex flex-wrap gap-2 text-gray-200"><span v-for="t in getPromotedFromPrevTally()" :key="t.username" class="bg-green-900/40 border border-green-800 px-2 py-1 rounded">{{ t.username }}: {{ t.vote_count }} 票</span></div></div><hr class="border-blue-800/50 my-3" /><div v-if="electionInfo.eliminated && electionInfo.eliminated.length > 0" class="flex items-start"><span class="text-red-400 font-bold w-16 shrink-0 mt-1">❌ 淘汰</span><div class="flex flex-wrap gap-2 text-gray-400"><span v-for="e in electionInfo.eliminated" :key="e.username" class="bg-red-900/20 border border-red-900/50 px-2 py-1 rounded line-through">{{ e.username }}: {{ e.vote_count }} 票</span></div></div></div>
                    <div class="flex justify-between items-end border-b border-gray-700 pb-2"><h2 class="text-2xl font-bold text-white">第 <span class="text-blue-400 text-3xl">{{ electionInfo.round_number }}</span> 轮投票</h2><span class="text-sm text-gray-400">请点选意向人选</span></div>
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
                      <div v-for="candidate in electionInfo.candidates" :key="candidate.id" @click="!userInfo.is_admin ? selectCandidate(candidate.id) : null" :class="['p-4 rounded-lg border transition-all duration-200 text-center flex flex-col items-center justify-center', userInfo.is_admin ? 'cursor-not-allowed opacity-75' : 'cursor-pointer', selectedId === candidate.id ? 'bg-blue-600/20 border-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]' : 'bg-gray-800 border-gray-600 hover:border-gray-400 hover:bg-gray-700']">
                        <img @click.stop="openLightbox(candidate.avatar_url)" :src="resolveAvatar(candidate.avatar_url)" class="w-12 h-12 rounded-full mb-2 object-cover border-2 border-gray-600 cursor-zoom-in hover:border-blue-400 transition" />
                        <div class="text-gray-200 font-medium text-sm">{{ candidate.username }}</div>
                      </div>
                    </div>
                    <div v-if="!userInfo.is_admin" class="flex space-x-4 pt-4"><button @click="submitVote(null)" class="w-1/3 bg-gray-700 hover:bg-gray-600 text-gray-300 font-bold py-3 px-4 rounded transition">弃 权</button><button @click="submitVote(selectedId)" :disabled="!selectedId" :class="['w-2/3 font-bold py-3 px-4 rounded transition text-white', selectedId ? 'bg-green-600 hover:bg-green-500' : 'bg-gray-600 cursor-not-allowed']">提交选票</button></div>
                    <p class="text-center text-sm" :class="sysMsg.includes('成功') ? 'text-green-400' : 'text-red-400'">{{ sysMsg }}</p>
                  </div>
                </div>
    
                <div v-if="activeMainTab === 'history'" class="p-6"><h2 class="text-xl font-bold text-white mb-4 flex items-center"><span class="mr-2">📚</span> 幻想乡历届当选档案</h2><div class="space-y-3"><div v-if="historyList.length === 0" class="text-center text-gray-500 py-8">暂无历史归档记录</div><div v-for="h in historyList" :key="h.year_month" class="bg-gray-800 border border-gray-600 p-4 rounded-lg flex justify-between items-center hover:border-blue-500 transition"><span class="text-gray-300 font-mono">{{ h.year_month }} 届</span><div class="flex items-center"><span class="text-sm text-gray-400 mr-2">胜出者:</span><span class="font-bold text-yellow-500 text-lg">{{ h.winner }}</span></div></div></div></div>
    
                <div v-if="activeMainTab === 'profile'" class="p-6">
                  <h2 class="text-2xl font-bold text-white mb-6 flex items-center"><span class="mr-2">🪪</span> 委员个人档案</h2>
                  <div class="flex flex-col md:flex-row gap-6">
                    <div class="bg-gray-800 p-5 rounded-lg border border-gray-700 w-full md:w-1/3 flex flex-col items-center">
                      <div class="relative group"><img @click="openLightbox(userInfo.avatar_url)" :src="resolveAvatar(userInfo.avatar_url)" class="w-28 h-28 rounded-full border-4 border-purple-500 object-cover cursor-zoom-in group-hover:opacity-80 transition shadow-[0_0_15px_rgba(168,85,247,0.4)]"><div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 pointer-events-none"><span class="bg-black/70 text-white text-xs px-2 py-1 rounded">查看大图</span></div></div>
                      <h3 class="mt-4 text-2xl font-bold text-white flex items-center">{{ userInfo.username }}<span v-if="userInfo.is_admin" class="ml-2 text-sm bg-indigo-600 text-white px-2 py-0.5 rounded">管理员</span></h3>
                      <p class="text-xs text-gray-500 font-mono mt-2 w-full text-center truncate px-2" :title="userInfo.id">UID: {{ userInfo.id }}</p>
                      <div class="mt-6 w-full pt-4 border-t border-gray-700">
                        <label class="block text-xs text-gray-400 mb-2">更新形象 (限制 5MB)</label>
                        <input type="file" ref="fileInput" @change="uploadLocalAvatar" accept="image/*" class="hidden">
                        <button @click="$refs.fileInput.click()" class="w-full bg-purple-600 hover:bg-purple-500 text-white text-sm py-2 rounded font-bold transition flex justify-center items-center"><span class="mr-2">📁</span> 选择本地图片上传</button>
                        <div class="flex items-center mt-3"><hr class="flex-grow border-gray-600"><span class="px-2 text-xs text-gray-500">或使用网络链接</span><hr class="flex-grow border-gray-600"></div>
                        <div class="flex mt-3 space-x-2"><input v-model="profileForm.avatar_url" type="text" placeholder="https://..." class="flex-1 bg-gray-900 text-white rounded px-2 border border-gray-600 text-xs focus:border-purple-500 outline-none"><button @click="updateAvatarUrl" class="bg-gray-700 hover:bg-gray-600 text-white text-xs px-3 rounded font-bold">直连</button></div>
                      </div>
                    </div>
                    <div class="w-full md:w-2/3 flex flex-col gap-6">
                      <div class="bg-gray-800 p-5 rounded-lg border border-gray-700"><h3 class="text-lg font-bold text-gray-200 mb-3 flex items-center"><span class="mr-2">🔑</span> 安全中心</h3><div class="grid grid-cols-1 sm:grid-cols-3 gap-2"><input v-model="profileForm.old_pwd" @keyup.enter="updatePassword" type="password" placeholder="当前密码" class="bg-gray-900 text-white rounded px-3 py-2 border border-gray-600 text-sm focus:border-purple-500 outline-none"><input v-model="profileForm.new_pwd" @keyup.enter="updatePassword" type="password" placeholder="新密码" class="bg-gray-900 text-white rounded px-3 py-2 border border-gray-600 text-sm focus:border-purple-500 outline-none"><input v-model="profileForm.confirm_pwd" @keyup.enter="updatePassword" type="password" placeholder="确认新密码" class="bg-gray-900 text-white rounded px-3 py-2 border border-gray-600 text-sm focus:border-purple-500 outline-none"></div><div class="mt-3 flex justify-between items-center"><p class="text-sm text-purple-400">{{ profileMsg }}</p><button @click="updatePassword" class="bg-red-600 hover:bg-red-500 text-white text-sm py-2 px-6 rounded font-bold transition">修改密码</button></div></div>
                      <div class="bg-gray-800 p-5 rounded-lg border border-gray-700 flex-1 flex flex-col"><h3 class="text-lg font-bold text-gray-200 mb-3 flex justify-between items-center"><span class="flex items-center"><span class="mr-2">📜</span> 政治履历 (投票记录)</span><button @click="fetchMyVotes" class="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded text-gray-300 transition">刷新记录</button></h3><div class="overflow-y-auto max-h-52 pr-2 space-y-2 flex-1 custom-scrollbar"><div v-if="myVotes.length === 0" class="text-sm text-gray-500 text-center py-8">暂无任何投票记录</div><div v-for="(v, i) in myVotes" :key="i" class="bg-gray-900/50 border border-gray-700 p-3 rounded flex justify-between items-center text-sm hover:border-purple-500 transition"><div><span class="text-blue-400 font-bold mr-2">{{ v.election_ym }} 届</span><span class="text-gray-400 text-xs">第 {{ v.round_num }} 轮</span></div><div class="flex items-center"><span class="text-gray-500 mr-3 text-xs hidden sm:inline">{{ v.vote_time }}</span><span :class="v.candidate_name === '弃权' ? 'text-gray-500' : 'text-green-400 font-bold'">{{ v.candidate_name === '弃权' ? '🤷 弃权' : '👉 ' + v.candidate_name }}</span></div></div></div></div>
                    </div>
                  </div>
                </div>
    
              </div>
            </transition>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue';
import axios from 'axios';

const defaultAvatar = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%234B5563"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>';
const wsConnected = ref(false);
const token = ref(localStorage.getItem('gensokyo_token') || '');
const isLoggedIn = ref(!!token.value);
const errorMessage = ref('');
const sysMsg = ref('');
const profileMsg = ref('');
const userInfo = ref({ is_admin: false, avatar_url: '' });

const chatOpen = ref(false);
const unreadCount = ref(0);
const chatMessages = ref([]);
const newChatMessage = ref('');
const chatBoxRef = ref(null);

const lightboxVisible = ref(false);
const lightboxUrl = ref('');
const openLightbox = (url) => { lightboxUrl.value = url; lightboxVisible.value = true; };

const resolveAvatar = (url) => {
  if (!url) return defaultAvatar;
  if (url.startsWith('http') || url.startsWith('data:')) return url;
  return url; 
};

const authMode = ref('login'); 
const activeMainTab = ref('vote'); 
const activeAdminTab = ref('election'); 

const containerHeight = ref('auto');

const onBeforeLeave = (el) => {
  containerHeight.value = el.offsetHeight + 'px';
};

const onEnter = (el) => {
  nextTick(() => {
    containerHeight.value = el.offsetHeight + 'px';
  });
};

const onAfterEnter = (el) => {
  containerHeight.value = 'auto';
};

const authForm = ref({ username: '', password: '', confirmPassword: '' }); 
const profileForm = ref({ avatar_url: '', old_pwd: '', new_pwd: '', confirm_pwd: '' });
const electionInfo = ref({ status: 'idle', round_number: 0, candidates: [], prev_tally: [], eliminated: [] });
const historyList = ref([]);
const myVotes = ref([]); 
const selectedId = ref(null);
const userList = ref([]);
const pendingCount = computed(() => userList.value.filter(u => !u.is_approved).length);
let ws = null;

let timeEngineTimer = null;
const nextElectionCountdown = ref('');
const electionElapsedSeconds = ref(0);
const EXPECTED_TOTAL_MINUTES = 60; 

const getNextElectionTarget = () => {
  const now = new Date();
  let target = new Date(now.getFullYear(), now.getMonth() + 1, 0, 16, 0, 0);
  if (now > target) target = new Date(now.getFullYear(), now.getMonth() + 2, 0, 16, 0, 0); 
  return target;
};

const progressDeg = computed(() => {
  const totalSeconds = EXPECTED_TOTAL_MINUTES * 60;
  let deg = (electionElapsedSeconds.value / totalSeconds) * 360;
  return deg > 360 ? 360 : deg;
});
const secondDeg = computed(() => (electionElapsedSeconds.value % 60) * 6);

const tickEngine = () => {
  const now = new Date();
  if (electionInfo.value.status === 'idle') {
    const target = getNextElectionTarget();
    const diff = target - now;
    if (diff > 0) {
      const d = Math.floor(diff / (1000 * 60 * 60 * 24));
      const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const m = Math.floor((diff / 1000 / 60) % 60);
      const s = Math.floor((diff / 1000) % 60);
      nextElectionCountdown.value = `${d}天 ${h.toString().padStart(2,'0')}小时 ${m.toString().padStart(2,'0')}分 ${s.toString().padStart(2,'0')}秒`;
    } else {
      nextElectionCountdown.value = "决选即将开启...";
    }
  } else if (electionInfo.value.start_time) {
    const startTime = new Date(electionInfo.value.start_time).getTime();
    let elapsed = Math.floor((now.getTime() - startTime) / 1000);
    if (elapsed < 0) elapsed = 0;
    electionElapsedSeconds.value = elapsed;
  }
};

const api = axios.create({ baseURL: `/api` });
api.interceptors.request.use(config => {
  if (token.value) config.headers.Authorization = `Bearer ${token.value}`;
  return config;
});

const getPromotedFromPrevTally = () => {
  if (!electionInfo.value.prev_tally || !electionInfo.value.eliminated) return [];
  return electionInfo.value.prev_tally.filter(
    c => !electionInfo.value.eliminated.some(e => e.username === c.username)
  );
};

const handleLogin = async () => {
  sysMsg.value = ''; errorMessage.value = '';
  try {
    const res = await api.post('/auth/login', authForm.value);
    token.value = res.data.access_token;
    localStorage.setItem('gensokyo_token', token.value);
    isLoggedIn.value = true;
    await fetchUserInfo();
    fetchCurrentElection();
    fetchChatHistory();
    fetchMyVotes();
    connectWebSocket();
  } catch (err) { errorMessage.value = err.response?.data?.detail || '登录失败'; }
};

const handleRegister = async () => {
  sysMsg.value = ''; errorMessage.value = '';
  if (!authForm.value.username || !authForm.value.password) return errorMessage.value = "账号密码不能为空";
  if (authForm.value.password !== authForm.value.confirmPassword) return errorMessage.value = "两次输入的密码不一致！";
  try {
    await api.post('/auth/register', authForm.value);
    sysMsg.value = "申请已提交！请等待最高委员会审批。";
    authForm.value = { username: '', password: '', confirmPassword: '' }; 
  } catch (err) { errorMessage.value = err.response?.data?.detail || '注册失败'; }
};

const logout = () => {
  localStorage.removeItem('gensokyo_token');
  token.value = ''; isLoggedIn.value = false; userInfo.value = { is_admin: false };
  if (ws) { ws.close(); ws = null; }
};

const fetchUserInfo = async () => {
  try { 
    const res = await api.get('/auth/me'); 
    userInfo.value = res.data; 
    profileForm.value.avatar_url = res.data.avatar_url || '';
    if (userInfo.value.is_admin) fetchUserList();
  } catch (err) { logout(); }
};

const uploadLocalAvatar = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);
  try {
    const res = await api.post('/auth/me/avatar/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    userInfo.value.avatar_url = res.data.avatar_url;
    alert("本地头像上传压缩成功！");
  } catch (e) { alert(e.response?.data?.detail || "上传失败"); }
  event.target.value = ''; 
};

const updateAvatarUrl = async () => {
  if(!profileForm.value.avatar_url) return;
  try {
    await api.put('/auth/me/avatar', { avatar_url: profileForm.value.avatar_url });
    userInfo.value.avatar_url = profileForm.value.avatar_url; 
    alert("网络头像连线成功！");
  } catch(e) { alert("更新失败"); }
};

const updatePassword = async () => {
  profileMsg.value = '';
  if (!profileForm.value.old_pwd || !profileForm.value.new_pwd) return profileMsg.value = "请填写完整";
  if (profileForm.value.new_pwd !== profileForm.value.confirm_pwd) return profileMsg.value = "两次输入的新密码不一致";
  try {
    await api.put('/auth/me/password', { old_password: profileForm.value.old_pwd, new_password: profileForm.value.new_pwd });
    profileMsg.value = "密码修改成功！";
    profileForm.value.old_pwd = ''; profileForm.value.new_pwd = ''; profileForm.value.confirm_pwd = '';
  } catch (e) { profileMsg.value = e.response?.data?.detail || "密码修改失败"; }
};

const fetchMyVotes = async () => {
  try { const res = await api.get('/auth/me/votes'); myVotes.value = res.data; } 
  catch (err) { console.error(err); }
};

const fetchCurrentElection = async () => {
  if (!isLoggedIn.value) return;
  try {
    const res = await api.get('/election/current');
    electionInfo.value = res.data;
    selectedId.value = null;
    tickEngine();
  } catch (err) { console.error(err); }
};

const fetchHistory = async () => {
  try { const res = await api.get('/election/history'); historyList.value = res.data; } 
  catch (err) { console.error(err); }
};

const fetchChatHistory = async () => {
  try {
    const res = await api.get('/chat/history');
    chatMessages.value = res.data;
    scrollToBottom();
  } catch (err) { console.error("拉取聊天记录失败", err); }
};

const sendChatMessage = async () => {
  if (!newChatMessage.value.trim()) return;
  const content = newChatMessage.value;
  newChatMessage.value = ''; 
  try {
    await api.post('/chat/send', { content });
  } catch (err) { alert("发送失败！"); }
};

const deleteChatMessage = async (id) => {
  if (!confirm("确定要强制删除这条消息吗？")) return;
  try {
    await api.delete(`/chat/${id}`);
  } catch (err) {
    alert(err.response?.data?.detail || "删除失败！");
  }
};

const toggleChat = () => {
  chatOpen.value = !chatOpen.value;
  if (chatOpen.value) {
    unreadCount.value = 0;
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBoxRef.value) {
      chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
    }
  });
};

const selectCandidate = (id) => {
  if (userInfo.value.is_admin) return;
  selectedId.value = id;
};

const submitVote = async (targetId) => {
  try {
    const res = await api.post('/election/vote', { candidate_id: targetId });
    sysMsg.value = res.data.message;
  } catch (err) { sysMsg.value = err.response?.data?.detail || '投票失败'; }
};

const adminStartElection = async () => { if(confirm("开启或重置本月选举？")) { try { await api.post('/election/debug/start_election'); sysMsg.value="已开启"; } catch(e){} }};
const adminTallyRound = async () => { if(confirm("结算当前轮次？")) { try { await api.post('/election/debug/tally_round'); sysMsg.value="已结算"; } catch(e){} }};
const adminArchive = async () => { if(confirm("关闭大结局页面？")) { try{ await api.post('/election/debug/archive'); } catch(e){} }};
const fetchUserList = async () => { try { const res = await api.get('/admin/users'); userList.value = res.data; } catch(e){} };
const adminApproveUser = async (u) => { try { await api.put(`/admin/users/${u.id}/approve`); fetchUserList(); } catch(e) {} };
const adminDeleteUser = async (u) => { if(confirm(`彻底除名 ${u.username}?`)) { try { await api.delete(`/admin/users/${u.id}`); fetchUserList(); } catch(e){} }};
const adminResetPassword = async (u) => { const pwd = prompt(`重置【${u.username}】的密码:`); if(pwd){ try { await api.put(`/admin/users/${u.id}/password`, {new_password:pwd}); alert('成功'); } catch(e){} }};

const connectWebSocket = () => {
  if (!isLoggedIn.value) return;
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/election`);
  ws.onopen = () => { wsConnected.value = true; };
  ws.onmessage = (event) => {
    let data = {};
    try { data = JSON.parse(event.data); } catch(e) {}
    
    if (data.event === "chat_message") {
      chatMessages.value.push(data.message);
      if (chatOpen.value) {
        scrollToBottom();
      } else {
        unreadCount.value++; 
      }
      return; 
    }
    
    if (data.event === "chat_message_deleted") {
      chatMessages.value = chatMessages.value.filter(m => m.id !== data.message_id);
      return; 
    }
    
    if (data.event === "user_list_updated") {
      if (userInfo.value.is_admin) fetchUserList(); 
      return; 
    }

    fetchCurrentElection(); 
    if(activeMainTab.value === 'history') fetchHistory();
    if(activeMainTab.value === 'profile') fetchMyVotes(); 
    sysMsg.value = "战况已同步！";
    setTimeout(() => sysMsg.value = '', 3000);
  };
  ws.onclose = () => { wsConnected.value = false; setTimeout(connectWebSocket, 3000); };
};

onMounted(() => {
  timeEngineTimer = setInterval(tickEngine, 1000);
  if (isLoggedIn.value) {
    fetchUserInfo().then(() => { 
        fetchCurrentElection(); 
        connectWebSocket(); 
        fetchMyVotes(); 
        fetchChatHistory();
    });
  }
});

onUnmounted(() => { 
  if (ws) ws.close(); 
  if (timeEngineTimer) clearInterval(timeEngineTimer);
});
</script>

<style scoped>
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  transform-origin: bottom right;
}
.fade-slide-enter-from, .fade-slide-leave-to {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}

.tab-fade-enter-active, .tab-fade-leave-active {
  transition: opacity 0.5s cubic-bezier(0.25, 1, 0.265, 1.15), 
              transform 0.5s cubic-bezier(0.25, 1, 0.265, 1.15);
}

.tab-fade-leave-active {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
}

.tab-fade-enter-from {
  opacity: 0;
  transform: translateY(15px);
}
.tab-fade-leave-to {
  opacity: 0;
  transform: translateY(-15px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.8);
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 1);
}
</style>