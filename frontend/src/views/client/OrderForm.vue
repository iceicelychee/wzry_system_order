<template>
  <div class="client-page">
    <div class="client-card">
      <div class="card-header">
        <h2>订单信息填写</h2>
      </div>

      <!-- 加载中 -->
      <div v-if="pageLoading" class="center-box">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <!-- 错误提示 -->
      <div v-else-if="errorMsg" class="center-box">
        <el-icon style="font-size:48px;color:#f56c6c"><CircleClose /></el-icon>
        <p style="color:#f56c6c;margin-top:12px">{{ errorMsg }}</p>
      </div>

      <!-- 已提交 - 自动跳转状态页面 -->
      <div v-else-if="alreadySubmitted" class="center-box">
        <el-icon style="font-size:48px;color:#67c23a"><CircleCheck /></el-icon>
        <p style="color:#67c23a;margin-top:12px">该订单已提交，正在跳转...</p>
      </div>

      <!-- 填写表单 -->
      <div v-else>
        <el-descriptions :column="1" border style="margin-bottom:24px">
          <el-descriptions-item label="订单编号">
            <strong>{{ orderNo }}</strong>
          </el-descriptions-item>
        </el-descriptions>

        <el-form :model="form" :rules="rules" ref="formRef" label-position="top">
          <el-form-item label="系统类型" prop="system_type">
            <el-select v-model="form.system_type" placeholder="请选择系统类型" size="large" style="width:100%">
              <el-option label="安卓Q区" value="安卓Q区" />
              <el-option label="苹果Q区" value="苹果Q区" />
              <el-option label="安卓V区" value="安卓V区" />
              <el-option label="苹果V区" value="苹果V区" />
            </el-select>
          </el-form-item>

          <el-form-item label="上传图片" prop="image">
            <div class="upload-section">
              <el-button icon="Upload" @click="triggerLocalUpload">本地上传</el-button>
              <input ref="fileInput" type="file" accept=".jpg,.jpeg,.png,.bmp,.gif,.webp"
                style="display:none" @change="handleFileSelect" />
              <el-button icon="Picture" @click="showGallery = true" style="margin-left:8px">图库选图</el-button>
            </div>
            <div v-if="previewUrl" class="preview-box">
              <el-image :src="previewUrl" :preview-src-list="[previewUrl]"
                style="width:120px;height:120px;border-radius:8px;margin-top:10px" fit="cover" />
              <el-button type="danger" link size="small" @click="clearImage" style="margin-left:8px">移除</el-button>
            </div>
            <div v-else class="upload-hint">支持 JPG / PNG / BMP，大小不超过 5MB，建议16:9比例</div>
          </el-form-item>

          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit"
            style="width:100%;margin-top:8px">
            提交订单
          </el-button>
        </el-form>
      </div>
    </div>

    <!-- 图片裁剪弹窗 -->
    <el-dialog v-model="showCropper" title="裁剪图片 (16:9)" width="92%" style="max-width:800px" :close-on-click-modal="false">
      <div class="cropper-container" v-if="cropperImage">
        <vue-cropper
          ref="cropperRef"
          :img="cropperImage"
          :output-size="1"
          :output-type="cropperExt || 'jpeg'"
          :info="true"
          :full="true"
          :can-move="true"
          :can-move-box="true"
          :fixed-box="false"
          :fixed="true"
          :fixed-number="[16, 9]"
          :center-box="true"
          :auto-crop="true"
          :auto-crop-width="640"
          :auto-crop-height="360"
          :mode="'contain'"
        />
      </div>
      <div class="cropper-toolbar">
        <el-button @click="rotateLeft"><el-icon><RefreshLeft /></el-icon> 左转</el-button>
        <el-button @click="rotateRight"><el-icon><RefreshRight /></el-icon> 右转</el-button>
        <el-button @click="resetCropper"><el-icon><Refresh /></el-icon> 重置</el-button>
        <el-button @click="zoomIn"><el-icon><ZoomIn /></el-icon> 放大</el-button>
        <el-button @click="zoomOut"><el-icon><ZoomOut /></el-icon> 缩小</el-button>
      </div>
      <template #footer>
        <el-button @click="cancelCrop">取消</el-button>
        <el-button type="primary" @click="confirmCrop">确认裁剪</el-button>
      </template>
    </el-dialog>

    <!-- 图库选图弹窗 -->
    <el-dialog v-model="showGallery" title="图库选图" width="92%" style="max-width:700px">
      <div class="gallery-filter">
        <el-select v-model="galleryFilter.category_id" placeholder="全部分类" clearable style="width:130px"
          @change="loadGallery">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-input v-model="galleryFilter.keyword" placeholder="搜索" clearable style="width:160px;margin-left:8px"
          prefix-icon="Search" @keyup.enter="loadGallery" />
      </div>
      <div class="gallery-grid" v-loading="galleryLoading">
        <div v-for="img in galleryList" :key="img.id" class="gallery-item"
          :class="{ selected: selectedId === img.id }" @click="selectedId = img.id; selectedImg = img">
          <el-image :src="getImageUrl(img.image_url)" fit="cover" style="width:100%;height:100%" />
          <div class="item-name">{{ img.name }}</div>
          <el-icon v-if="selectedId === img.id" class="check-mark"><Check /></el-icon>
        </div>
        <el-empty v-if="!galleryList.length && !galleryLoading" description="暂无图片" style="grid-column:1/-1" />
      </div>
      <template #footer>
        <el-button @click="showGallery = false">取消</el-button>
        <el-button type="primary" :disabled="!selectedId" @click="confirmGallery">确认选择</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { clientApi, galleryApi, getImageUrl } from '../../api'
import 'vue-cropper/dist/index.css'
import { VueCropper } from 'vue-cropper'

const route = useRoute()
const router = useRouter()
const token = route.params.token

const pageLoading = ref(true)
const errorMsg = ref('')
const alreadySubmitted = ref(false)
const orderNo = ref('')
const submitting = ref(false)
const formRef = ref()
const fileInput = ref()

const form = reactive({ system_type: '', image: null })
const previewUrl = ref('')

const rules = {
  system_type: [{ required: true, message: '请选择系统类型', trigger: 'change' }],
  image: [{ validator: (r, v, cb) => form.image ? cb() : cb(new Error('请上传图片')), trigger: 'change' }],
}

// 裁剪相关
const showCropper = ref(false)
const cropperImage = ref('')
const cropperExt = ref('jpeg')
const cropperRef = ref()
const pendingFile = ref(null)

const showGallery = ref(false)
const galleryLoading = ref(false)
const galleryList = ref([])
const categories = ref([])
const galleryFilter = reactive({ category_id: null, keyword: '' })
const selectedId = ref(null)
const selectedImg = ref(null)

onMounted(async () => {
  try {
    const res = await clientApi.getOrder(token)
    orderNo.value = res.order_no
    alreadySubmitted.value = res.already_submitted
    // 已提交订单直接跳转到状态页面
    if (res.already_submitted) {
      router.push(`/order/${token}/status`)
      return
    }
    if (res.system_type) form.system_type = res.system_type
  } catch (e) {
    errorMsg.value = e.response?.data?.detail || '链接无效或已失效'
  } finally {
    pageLoading.value = false
  }
  const cats = await galleryApi.categoryList()
  categories.value = cats
  loadGallery()
})

async function loadGallery() {
  galleryLoading.value = true
  try {
    const params = { page: 1, page_size: 50 }
    if (galleryFilter.category_id) params.category_id = galleryFilter.category_id
    if (galleryFilter.keyword) params.keyword = galleryFilter.keyword
    const res = await galleryApi.list(params)
    galleryList.value = res.list
  } finally {
    galleryLoading.value = false
  }
}

function triggerLocalUpload() { fileInput.value.click() }

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.error('图片不能超过5MB'); return }

  // 获取文件扩展名
  const ext = file.name.split('.').pop().toLowerCase()
  cropperExt.value = ext === 'png' ? 'png' : 'jpeg'
  pendingFile.value = file

  // 读取文件为 base64 用于裁剪
  const reader = new FileReader()
  reader.onload = (e) => {
    cropperImage.value = e.target.result
    showCropper.value = true
  }
  reader.readAsDataURL(file)
}

// 裁剪工具栏功能
function rotateLeft() { cropperRef.value?.rotateLeft() }
function rotateRight() { cropperRef.value?.rotateRight() }
function resetCropper() { cropperRef.value?.refresh() }
function zoomIn() { cropperRef.value?.changeScale(1) }
function zoomOut() { cropperRef.value?.changeScale(-1) }

function cancelCrop() {
  showCropper.value = false
  cropperImage.value = ''
  pendingFile.value = null
  if (fileInput.value) fileInput.value.value = ''
}

function confirmCrop() {
  if (!cropperRef.value) return

  cropperRef.value.getCropBlob((blob) => {
    const fileName = pendingFile.value ? pendingFile.value.name : `cropped.${cropperExt.value}`
    const croppedFile = new File([blob], fileName, { type: `image/${cropperExt.value}` })

    form.image = croppedFile
    previewUrl.value = URL.createObjectURL(blob)
    showCropper.value = false
    cropperImage.value = ''
    pendingFile.value = null
    ElMessage.success('裁剪完成')
  })
}

function clearImage() {
  form.image = null
  previewUrl.value = ''
  selectedId.value = null
  selectedImg.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function confirmGallery() {
  if (!selectedImg.value) return
  try {
    const res = await fetch(getImageUrl(selectedImg.value.image_url))
    const blob = await res.blob()
    form.image = new File([blob], selectedImg.value.name + '.jpg', { type: blob.type })
    previewUrl.value = getImageUrl(selectedImg.value.image_url)
    showGallery.value = false
  } catch {
    ElMessage.error('图片加载失败，请尝试本地上传')
  }
}

async function handleSubmit() {
  await formRef.value.validate()
  if (!form.image) { ElMessage.error('请上传图片'); return }
  submitting.value = true
  try {
    const fd = new FormData()
    fd.append('system_type', form.system_type)
    fd.append('image', form.image)
    await clientApi.submit(token, fd)
    ElMessage.success('提交成功！')
    router.push(`/order/${token}/status`)
  } finally {
    submitting.value = false
  }
}

function goStatus() { router.push(`/order/${token}/status`) }
</script>

<style scoped>
.client-page {
  min-height: 100vh;
  background: #f0f2f5;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 24px 16px;
}
.client-card {
  background: #fff;
  border-radius: 12px;
  padding: 28px 24px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.card-header { text-align: center; margin-bottom: 24px; }
.card-header h2 { font-size: 20px; color: #303133; margin: 0; }
.center-box { text-align: center; padding: 32px 0; }
.loading-icon { font-size: 40px; color: #409eff; animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.upload-section { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.upload-hint { color: #909399; font-size: 12px; margin-top: 6px; }
.preview-box { display: flex; align-items: center; }
.gallery-filter { display: flex; margin-bottom: 14px; }
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  max-height: 380px;
  overflow-y: auto;
}
.gallery-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
}
.gallery-item:hover { border-color: #409eff; }
.gallery-item.selected { border-color: #409eff; }
.item-name {
  position: absolute; bottom: 0; left: 0; right: 0;
  background: rgba(0,0,0,0.5); color: #fff;
  font-size: 11px; padding: 3px 5px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.check-mark {
  position: absolute; top: 4px; right: 4px;
  background: #409eff; color: #fff; border-radius: 50%; padding: 2px; font-size: 13px;
}

/* 裁剪器样式 */
.cropper-container {
  height: 400px;
  background: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
}
.cropper-toolbar {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}
</style>
