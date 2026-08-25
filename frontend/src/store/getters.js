const getters = {
  sidebar: state => state.app.sidebar,
  device: state => state.app.device,
  token: state => state.user.token,
  avatar: state => state.user.avatar,
  name: state => state.user.name,
  nickname: state => state.user.nickname,
  userid: state => state.user.userid,
  email: state => state.user.email,
  permissions: state => state.user.permissions,
  warnLog: state => state.user.warnLog,
  loginLocation: state => state.user.loginLocation,
  theme: state => state.user.theme,
  dashBoardFullScreen: state => state.user.dashBoardFullScreen,
  gridDiagramNum: state => state.user.gridDiagramNum,
  resultAllRoutes: state => state.user.resultAllRoutes,
  sidebarStatus: state => state.app.sidebar.opened,
  dict: state => state.dict.dict,
  sideTheme: state => state.settings.sideTheme
}
export default getters
