ARG ALPINE_VERSION=3.12
ARG PYTHON_VERSION=3

FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION}

ARG TASK_VERSION=v2.5.1
ARG VIM_VERSION=v8.2.0716
ARG VIMWIKI_VERSION=master

RUN set -ex \
 && apk add --no-cache --virtual .taskwiki-test-deps \
    git \
    make \
    tzdata \
    xvfb-run \
 && ln -sf /usr/share/zoneinfo/Etc/UTC /etc/localtime \
 && true

RUN set -ex \
 \
 && : install vim $VIM_VERSION \
 \
 && apk add --no-cache --virtual .vim-build-deps \
    gcc \
    git \
    gtk+3.0-dev \
    libxt-dev \
    make \
    musl-dev \
    ncurses-dev \
    patchelf \
 && cd /usr/src \
 && git clone --depth 1 --recurse-submodules --shallow-submodules --branch $VIM_VERSION \
    https://github.com/vim/vim \
 && cd vim \
 && sed -i -e '/#\s*undef _POSIX_THREADS/d' src/if_python3.c \
 && ./configure --prefix=/opt/vim --enable-pythoninterp --enable-python3interp --enable-gui=gtk3 \
 && make -j$(nproc) \
 && make install \
 && rm -rf /usr/src/vim \
 && patchelf --print-needed /opt/vim/bin/* \
  | grep -v '^libpython' \
  | sort -u \
  | sed -e 's/^/so:/' \
  | xargs -rt apk add --no-cache --virtual .vim-runtime-deps \
 \
 && : install taskwarrior $TASK_VERSION \
 \
 && apk add --no-cache --virtual .taskwarrior-build-deps \
    cmake \
    g++ \
    gcc \
    git \
    make \
    patchelf \
    util-linux-dev \
 && cd /usr/src \
 && git clone --depth 1 --recurse-submodules --shallow-submodules --branch $TASK_VERSION \
    https://github.com/GothenburgBitFactory/taskwarrior \
 && cd taskwarrior \
 && cmake -DCMAKE_INSTALL_PREFIX=/opt/taskwarrior -DCMAKE_BUILD_TYPE=release -DENABLE_SYNC=OFF . \
 && make -j$(nproc) \
 && make install \
 && rm -rf /usr/src/taskwarrior \
 && patchelf --print-needed /opt/taskwarrior/bin/* \
  | sort -u \
  | sed -e 's/^/so:/' \
  | xargs -rt apk add --no-cache --virtual .taskwarrior-runtime-deps \
 \
 && : install vimwiki $VIMWIKI_VERSION \
 \
 && mkdir -p /root/.vim/bundle \
 && cd /root/.vim/bundle \
 && git clone --depth 1 --recurse-submodules --shallow-submodules --branch $VIMWIKI_VERSION \
    https://github.com/vimwiki/vimwiki \
 \
 && : install python test dependencies \
 \
 && apk add --no-cache --virtual .python-coverage-build-deps \
    gcc \
    musl-dev \
 && pip install \
    coverage \
    coveralls \
    pytest \
    pytest-cov \
    pytest-xdist \
    https://github.com/liskin/vimrunner-python/archive/8c19ff88050c09236e7519425bfae33c687483df.zip \
 \
 && : clean up build dependencies \
 \
 && apk del --no-network .taskwarrior-build-deps \
 && apk del --no-network .vim-build-deps \
 && apk del --no-network .python-coverage-build-deps \
 && true

ENV PATH=/opt/vim/bin:/opt/taskwarrior/bin:$PATH
RUN set -ex \
 && task --version \
 && vim --version \
 && true

COPY requirements.txt /root/.vim/bundle/taskwiki/
RUN pip install -r /root/.vim/bundle/taskwiki/requirements.txt
WORKDIR /root/.vim/bundle/taskwiki
