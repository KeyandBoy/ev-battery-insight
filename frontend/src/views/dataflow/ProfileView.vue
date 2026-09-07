<script setup>
import { computed, reactive } from "vue";
import { ElMessage } from "element-plus";

import { updatePassword } from "../../api/dataflow/auth";
import { useAuthStore } from "../../stores/dataflow/auth";
import { resolveBackendUrl } from "../../utils/dataflow/url";

const authStore = useAuthStore();

const profileForm = reactive({
  username: authStore.user?.username || "",
  display_name: authStore.user?.display_name || "",
  email: authStore.user?.email || "",
  bio: authStore.user?.bio || "",
  avatar_url: authStore.user?.avatar_url || "",
});

const passwordForm = reactive({
  old_password: "",
  new_password: "",
});

const avatarPreview = computed(() => resolveBackendUrl(profileForm.avatar_url || ""));

async function handleSaveProfile() {
  try {
    const result = await authStore.saveProfile(profileForm);
    profileForm.username = result.data.username || "";
    profileForm.display_name = result.data.display_name || "";
    profileForm.email = result.data.email || "";
    profileForm.bio = result.data.bio || "";
    profileForm.avatar_url = result.data.avatar_url || "";
    ElMessage.success("个人资料已保存");
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function handleSaveAvatarUrl() {
  try {
    const result = await authStore.saveProfile({ avatar_url: profileForm.avatar_url });
    profileForm.avatar_url = result.data.avatar_url || "";
    ElMessage.success("头像地址已更新");
  } catch (error) {
    ElMessage.error(error.message);
  }
}

async function uploadAvatarRequest(options) {
  try {
    const result = await authStore.saveAvatar(options.file);
    profileForm.avatar_url = result?.data?.avatar_url || "";
    ElMessage.success("头像上传成功");
    options.onSuccess(result);
  } catch (error) {
    options.onError(error);
    ElMessage.error(error.message);
  }
}

function beforeAvatarUpload(file) {
  const isImage = file.type.startsWith("image/");
  const isLt5m = file.size / 1024 / 1024 < 5;
  if (!isImage) {
    ElMessage.error("请上传图片文件");
    return false;
  }
  if (!isLt5m) {
    ElMessage.error("图片大小不能超过 5MB");
    return false;
  }
  return true;
}

async function handleChangePassword() {
  try {
    await updatePassword(passwordForm);
    passwordForm.old_password = "";
    passwordForm.new_password = "";
    ElMessage.success("密码修改成功");
  } catch (error) {
    ElMessage.error(error.message);
  }
}
</script>

<template>
  <div class="page-wrap">
    <el-row :gutter="16">
      <el-col :xs="24" :md="8">
        <el-card shadow="never">
          <template #header>
            <span>头像设置</span>
          </template>
          <div class="profile-avatar-box">
            <el-avatar :size="120" :src="avatarPreview">
              {{ (profileForm.display_name || profileForm.username || "U").slice(0, 1) }}
            </el-avatar>
          </div>
          <el-form label-position="top">
            <el-form-item label="头像URL">
              <el-input v-model="profileForm.avatar_url" placeholder="https://example.com/avatar.png" />
            </el-form-item>
            <el-button type="primary" plain @click="handleSaveAvatarUrl">保存URL头像</el-button>
          </el-form>
          <el-divider />
          <el-upload
            :http-request="uploadAvatarRequest"
            :show-file-list="false"
            :before-upload="beforeAvatarUpload"
            accept=".png,.jpg,.jpeg,.webp,.gif"
          >
            <el-button type="primary">上传本地头像</el-button>
          </el-upload>
        </el-card>
      </el-col>

      <el-col :xs="24" :md="16">
        <el-card shadow="never">
          <template #header>
            <span>个人资料</span>
          </template>
          <el-form label-position="top">
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="用户名">
                  <el-input v-model="profileForm.username" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="显示名称">
                  <el-input v-model="profileForm.display_name" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="邮箱">
                  <el-input v-model="profileForm.email" />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="账号状态">
                  <el-input :value="authStore.user?.status === 1 ? '启用' : '禁用'" disabled />
                </el-form-item>
              </el-col>
              <el-col :xs="24">
                <el-form-item label="个人简介">
                  <el-input v-model="profileForm.bio" type="textarea" :rows="4" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-button type="primary" @click="handleSaveProfile">保存资料</el-button>
          </el-form>
        </el-card>

        <el-card shadow="never" style="margin-top: 16px">
          <template #header>
            <span>修改密码</span>
          </template>
          <el-form label-position="top">
            <el-row :gutter="12">
              <el-col :xs="24" :sm="12">
                <el-form-item label="旧密码">
                  <el-input v-model="passwordForm.old_password" type="password" show-password />
                </el-form-item>
              </el-col>
              <el-col :xs="24" :sm="12">
                <el-form-item label="新密码">
                  <el-input v-model="passwordForm.new_password" type="password" show-password />
                </el-form-item>
              </el-col>
            </el-row>
            <el-button type="primary" plain @click="handleChangePassword">更新密码</el-button>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
