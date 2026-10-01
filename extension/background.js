// 收到按键的那个框架不一定有视频（很多播放器在内嵌框架里），所以转发给这个标签页的所有框架。
chrome.runtime.onMessage.addListener((command, sender) => {
  if (sender.tab) chrome.tabs.sendMessage(sender.tab.id, command).catch(() => {});
});
