FROM fedora:27
ARG TASK_VERSION

RUN dnf update -y
RUN dnf install procps-ng psmisc which vim curl git gvim gcc gcc-c++ cmake make gnutls-devel libuuid-devel -y

# Setup language environment
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Setup taskwarrior
RUN git clone --recursive https://github.com/GothenburgBitFactory/taskwarrior.git task
WORKDIR task
RUN echo ${TASK_VERSION}; git checkout ${TASK_VERSION}
RUN git clean -dfx
RUN git submodule init
RUN git submodule update
RUN cmake -DCMAKE_BUILD_TYPE=release .
RUN make -j2
RUN make install
RUN task --version

# Setup vimwiki
RUN mkdir -p /root/.vim/bundle /root/.vim/autoload
RUN curl -LSso ~/.vim/autoload/pathogen.vim https://tpo.pe/pathogen.vim
RUN cd /root/.vim/bundle; git clone https://github.com/vimwiki/vimwiki.git
RUN cd /root/.vim/bundle/vimwiki/; git checkout dev

# Setup taskwiki
RUN pip3 install nose pytest coveralls coverage vimrunner
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN mkdir /root/.vim/bundle/taskwiki
WORKDIR /root/.vim/bundle/taskwiki

CMD ["sh", "-c", "python3 -m pytest -vv tests/"]
